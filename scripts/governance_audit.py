#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, hmac, json, os, shutil, subprocess, tempfile
from pathlib import Path
from typing import Any
import yaml

ZERO_HASH = "sha256:" + ("0" * 64)
HMAC_ALG = "HMAC-SHA256"
CHECKPOINT_ALG = "Ed25519"
SET_LIKE_KEYS = {"files", "boundaries", "operations", "evidence_digests"}
DEFAULT_HMAC_ENV = "AIPS_GOVERNANCE_AUDIT_HMAC_KEY"

def canonicalize(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {k: canonicalize(value[k], k) for k in sorted(value)}
    if isinstance(value, list):
        items = [canonicalize(v) for v in value]
        if key in SET_LIKE_KEYS:
            return sorted(items, key=lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True))
        return items
    return value

def canonical_json(value: Any) -> str:
    return json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()

def load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) if path.suffix.lower() in {".yaml", ".yml"} else json.loads(text)
    data = data or {}
    if not isinstance(data, dict):
        raise ValueError("event input must be a mapping")
    return data

def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"ledger line {line_no} is not valid JSON: {exc}") from exc
        if not isinstance(item, dict):
            raise ValueError(f"ledger line {line_no} must be a JSON object")
        events.append(item)
    return events

def event_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in event.items() if k != "integrity"}

def event_hash(event: dict[str, Any]) -> str:
    return sha256_text(canonical_json(event_payload(event)))

def chain_hash(previous_chain_hash: str, current_event_hash: str) -> str:
    return sha256_text(canonical_json({"previous_chain_hash": previous_chain_hash, "event_hash": current_event_hash}))

def hmac_value(secret: str, chain: str, sequence: int, key_id: str) -> str:
    message = canonical_json({"chain_hash": chain, "sequence": sequence, "key_id": key_id}).encode("utf-8")
    return "hmac-sha256:" + hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

def public_key_fingerprint(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def _openssl() -> str:
    binary = shutil.which("openssl")
    if not binary:
        raise RuntimeError("OpenSSL is required for Ed25519 checkpoint signing/verification")
    return binary

def sign_checkpoint(private_key: Path, chain: str) -> str:
    with tempfile.NamedTemporaryFile() as message, tempfile.NamedTemporaryFile() as signature:
        message.write(chain.encode("utf-8")); message.flush()
        result = subprocess.run([_openssl(), "pkeyutl", "-sign", "-rawin", "-inkey", str(private_key),
                                 "-in", message.name, "-out", signature.name],
                                capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            raise RuntimeError("Ed25519 checkpoint signing failed: " + (result.stderr.strip() or result.stdout.strip()))
        return base64.b64encode(Path(signature.name).read_bytes()).decode("ascii")

def verify_checkpoint(public_key: Path, chain: str, signature_b64: str) -> bool:
    try:
        signature = base64.b64decode(signature_b64, validate=True)
    except Exception:
        return False
    with tempfile.NamedTemporaryFile() as message, tempfile.NamedTemporaryFile() as sig:
        message.write(chain.encode("utf-8")); message.flush()
        sig.write(signature); sig.flush()
        result = subprocess.run([_openssl(), "pkeyutl", "-verify", "-rawin", "-pubin", "-inkey", str(public_key),
                                 "-in", message.name, "-sigfile", sig.name],
                                capture_output=True, text=True, timeout=15)
        return result.returncode == 0

def normalize_event_input(raw: dict[str, Any], sequence: int) -> dict[str, Any]:
    if {"sequence", "integrity"}.intersection(raw):
        raise ValueError("event input must not set sequence or integrity")
    if not str(raw.get("event_type") or "").strip():
        raise ValueError("event_type is required")
    if not str(raw.get("occurred_at") or "").strip():
        raise ValueError("occurred_at is required")
    event = dict(raw)
    event["version"] = int(event.get("version") or 1)
    event["sequence"] = sequence
    if not event.get("event_id"):
        identity = {k: v for k, v in event.items() if k != "event_id"}
        event["event_id"] = "evt-" + hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()[:24]
    return event

def verify_events(events: list[dict[str, Any]], *, hmac_secrets: dict[str, str] | None = None,
                  checkpoint_public_keys: dict[str, Path] | None = None,
                  require_authenticated_verification: bool = False,
                  require_checkpoint_verification: bool = False,
                  expected_chain_head: str | None = None,
                  expected_events: int | None = None) -> dict[str, Any]:
    errors = []; previous = ZERO_HASH; seen_ids = set()
    hmac_secrets = hmac_secrets or {}; checkpoint_public_keys = checkpoint_public_keys or {}
    authenticated_events = verified_hmac_events = checkpoint_events = verified_checkpoints = 0
    for expected_sequence, event in enumerate(events, start=1):
        if event.get("sequence") != expected_sequence:
            errors.append(f"sequence mismatch at position {expected_sequence}: {event.get('sequence')!r}")
        event_id = str(event.get("event_id") or "")
        if not event_id:
            errors.append(f"event {expected_sequence} missing event_id")
        elif event_id in seen_ids:
            errors.append(f"duplicate event_id: {event_id}")
        seen_ids.add(event_id)
        integrity = event.get("integrity") or {}
        if integrity.get("previous_chain_hash") != previous:
            errors.append(f"event {expected_sequence} previous_chain_hash mismatch")
        expected_event_hash = event_hash(event)
        if integrity.get("event_hash") != expected_event_hash:
            errors.append(f"event {expected_sequence} event_hash mismatch")
        expected_chain = chain_hash(previous, expected_event_hash)
        if integrity.get("chain_hash") != expected_chain:
            errors.append(f"event {expected_sequence} chain_hash mismatch")
        auth = integrity.get("authentication") or {}
        if auth.get("status") == "AUTHENTICATED":
            authenticated_events += 1
            key_id = str(auth.get("key_id") or "")
            hmac_material = hmac_secrets.get(key_id)
            if hmac_material is None:
                if require_authenticated_verification:
                    errors.append(f"event {expected_sequence} HMAC key unavailable: {key_id}")
            else:
                expected_mac = hmac_value(hmac_material, expected_chain, expected_sequence, key_id)
                if not hmac.compare_digest(str(auth.get("mac") or ""), expected_mac):
                    errors.append(f"event {expected_sequence} HMAC mismatch")
                else:
                    verified_hmac_events += 1
        elif auth.get("status") != "NOT_CONFIGURED":
            errors.append(f"event {expected_sequence} invalid authentication status")
        checkpoint = integrity.get("checkpoint")
        if checkpoint:
            checkpoint_events += 1
            if checkpoint.get("algorithm") != CHECKPOINT_ALG:
                errors.append(f"event {expected_sequence} unsupported checkpoint algorithm")
            key_id = str(checkpoint.get("key_id") or "")
            key_path = checkpoint_public_keys.get(key_id)
            if key_path is None:
                if require_checkpoint_verification:
                    errors.append(f"event {expected_sequence} checkpoint public key unavailable: {key_id}")
            elif checkpoint.get("public_key_fingerprint") != public_key_fingerprint(key_path):
                errors.append(f"event {expected_sequence} checkpoint public key fingerprint mismatch")
            elif not verify_checkpoint(key_path, expected_chain, str(checkpoint.get("signature_b64") or "")):
                errors.append(f"event {expected_sequence} checkpoint signature mismatch")
            else:
                verified_checkpoints += 1
        previous = expected_chain
    actual_head = previous if events else ZERO_HASH
    if expected_events is not None and len(events) != expected_events:
        errors.append(f"event count mismatch: expected={expected_events} actual={len(events)}")
    if expected_chain_head is not None and actual_head != expected_chain_head:
        errors.append(f"chain head mismatch: expected={expected_chain_head} actual={actual_head}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "events": len(events),
        "chain_head": actual_head,
        "authentication": {"authenticated_events": authenticated_events, "verified_hmac_events": verified_hmac_events,
                           "unverified_hmac_events": authenticated_events - verified_hmac_events},
        "checkpoints": {"checkpoint_events": checkpoint_events, "verified_checkpoints": verified_checkpoints,
                        "unverified_checkpoints": checkpoint_events - verified_checkpoints},
        "errors": errors,
    }

def append_event(ledger: Path, raw_event: dict[str, Any], *, hmac_key_env: str | None = None,
                 hmac_key_id: str | None = None, checkpoint_private_key: Path | None = None,
                 checkpoint_public_key: Path | None = None, checkpoint_key_id: str | None = None,
                 verification_hmac_secrets: dict[str, str] | None = None,
                 verification_public_keys: dict[str, Path] | None = None,
                 verification_expected_chain_head: str | None = None,
                 verification_expected_events: int | None = None) -> dict[str, Any]:
    existing = read_ledger(ledger)
    if existing or verification_expected_chain_head is not None or verification_expected_events is not None:
        verification = verify_events(existing, hmac_secrets=verification_hmac_secrets,
                                     checkpoint_public_keys=verification_public_keys,
                                     require_authenticated_verification=True,
                                     require_checkpoint_verification=True,
                                     expected_chain_head=verification_expected_chain_head,
                                     expected_events=verification_expected_events)
        if verification["status"] != "PASS":
            raise ValueError("refusing to append to invalid ledger: " + "; ".join(verification["errors"]))
    sequence = len(existing) + 1
    previous = (existing[-1].get("integrity") or {}).get("chain_hash") if existing else ZERO_HASH
    event = normalize_event_input(raw_event, sequence)
    current_event_hash = event_hash(event); current_chain_hash = chain_hash(previous, current_event_hash)
    integrity: dict[str, Any] = {
        "previous_chain_hash": previous, "event_hash": current_event_hash, "chain_hash": current_chain_hash,
        "authentication": {"algorithm": HMAC_ALG, "status": "NOT_CONFIGURED", "key_id": None, "mac": None},
        "checkpoint": None,
    }
    env_name = hmac_key_env or DEFAULT_HMAC_ENV
    key_id = (hmac_key_id or "").strip()
    if key_id:
        hmac_material = os.environ.get(env_name)
        if hmac_material is None:
            raise ValueError(f"HMAC secret environment variable is not configured: {env_name}")
        integrity["authentication"] = {"algorithm": HMAC_ALG, "status": "AUTHENTICATED", "key_id": key_id,
                                       "mac": hmac_value(hmac_material, current_chain_hash, sequence, key_id)}
    if checkpoint_private_key is not None:
        if checkpoint_public_key is None:
            raise ValueError("checkpoint_public_key is required with checkpoint_private_key")
        checkpoint_id = (checkpoint_key_id or "").strip()
        if not checkpoint_id:
            raise ValueError("checkpoint_key_id is required for signed checkpoints")
        integrity["checkpoint"] = {"algorithm": CHECKPOINT_ALG, "key_id": checkpoint_id,
                                   "public_key_fingerprint": public_key_fingerprint(checkpoint_public_key),
                                   "signature_b64": sign_checkpoint(checkpoint_private_key, current_chain_hash)}
    event["integrity"] = integrity
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(event) + "\n")
    return event

def parse_key_bindings(values: list[str]) -> dict[str, str]:
    result = {}
    for value in values:
        if "=" not in value:
            raise ValueError("key binding must be KEY_ID=ENV_NAME")
        key_id, env_name = value.split("=", 1); hmac_material = os.environ.get(env_name)
        if hmac_material is None:
            raise ValueError(f"environment variable not configured: {env_name}")
        result[key_id] = hmac_material
    return result

def parse_public_keys(values: list[str]) -> dict[str, Path]:
    result = {}
    for value in values:
        if "=" not in value:
            raise ValueError("public key binding must be KEY_ID=PATH")
        key_id, path = value.split("=", 1); result[key_id] = Path(path).expanduser().resolve()
    return result

def emit(doc: dict[str, Any]) -> None:
    print(json.dumps(doc, ensure_ascii=False, indent=2))

def main() -> int:
    parser = argparse.ArgumentParser(description="AIPS tamper-evident governance audit ledger")
    sub = parser.add_subparsers(dest="command", required=True)
    append = sub.add_parser("append")
    append.add_argument("--ledger", required=True); append.add_argument("--event", required=True)
    append.add_argument("--hmac-key-env", default=DEFAULT_HMAC_ENV); append.add_argument("--hmac-key-id")
    append.add_argument("--checkpoint-private-key"); append.add_argument("--checkpoint-public-key")
    append.add_argument("--checkpoint-key-id")
    append.add_argument("--verify-hmac", action="append", default=[], metavar="KEY_ID=ENV_NAME")
    append.add_argument("--verify-checkpoint-public-key", action="append", default=[], metavar="KEY_ID=PATH")
    append.add_argument("--expected-chain-head")
    append.add_argument("--expected-events", type=int)
    verify = sub.add_parser("verify")
    verify.add_argument("--ledger", required=True)
    verify.add_argument("--hmac", action="append", default=[], metavar="KEY_ID=ENV_NAME")
    verify.add_argument("--checkpoint-public-key", action="append", default=[], metavar="KEY_ID=PATH")
    verify.add_argument("--require-auth-verification", action="store_true")
    verify.add_argument("--require-checkpoint-verification", action="store_true")
    verify.add_argument("--expected-chain-head")
    verify.add_argument("--expected-events", type=int)
    args = parser.parse_args()
    try:
        ledger = Path(args.ledger).expanduser().resolve()
        if args.command == "append":
            verification_hmac = parse_key_bindings(args.verify_hmac)
            configured_secret = os.environ.get(args.hmac_key_env)
            if configured_secret and args.hmac_key_id:
                verification_hmac.setdefault(args.hmac_key_id, configured_secret)
            doc = append_event(
                ledger, load_mapping(Path(args.event).expanduser().resolve()),
                hmac_key_env=args.hmac_key_env, hmac_key_id=args.hmac_key_id,
                checkpoint_private_key=Path(args.checkpoint_private_key).expanduser().resolve() if args.checkpoint_private_key else None,
                checkpoint_public_key=Path(args.checkpoint_public_key).expanduser().resolve() if args.checkpoint_public_key else None,
                checkpoint_key_id=args.checkpoint_key_id, verification_hmac_secrets=verification_hmac,
                verification_public_keys=parse_public_keys(args.verify_checkpoint_public_key),
                verification_expected_chain_head=args.expected_chain_head,
                verification_expected_events=args.expected_events,
            )
            emit({"status": "APPENDED", "event_id": doc["event_id"], "sequence": doc["sequence"],
                  "chain_hash": doc["integrity"]["chain_hash"],
                  "authentication": doc["integrity"]["authentication"]["status"],
                  "checkpoint": bool(doc["integrity"]["checkpoint"])})
            return 0
        result = verify_events(read_ledger(ledger), hmac_secrets=parse_key_bindings(args.hmac),
                               checkpoint_public_keys=parse_public_keys(args.checkpoint_public_key),
                               require_authenticated_verification=args.require_auth_verification,
                               require_checkpoint_verification=args.require_checkpoint_verification,
                               expected_chain_head=args.expected_chain_head,
                               expected_events=args.expected_events)
        emit(result); return 0 if result["status"] == "PASS" else 2
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, yaml.YAMLError, subprocess.TimeoutExpired) as exc:
        emit({"status": "FAIL", "errors": [str(exc)]}); return 2

if __name__ == "__main__":
    raise SystemExit(main())
