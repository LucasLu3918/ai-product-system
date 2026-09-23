#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, hmac, json, os, re, shutil, subprocess, tempfile
from pathlib import Path
from typing import Any
import yaml

try:
    from content_safety import safe_emit
except ModuleNotFoundError:  # imported as a repository module
    from scripts.content_safety import safe_emit

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
    safety = safe_emit(sink="governance_audit", payload=raw_event)
    if safety["decision"] == "BLOCK":
        raise ValueError("content safety blocked governance audit event")
    raw_event = safety["safe_payload"]
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


BUNDLE_TYPE = "aips-governance-audit-bundle"
BUNDLE_MANIFEST = "MANIFEST.json"
BUNDLE_ANCHOR = "ANCHOR.json"
BUNDLE_LEDGER = "AUDIT.jsonl"
SAFE_BUNDLE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()

def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())

def safe_bundle_name(value: str, field: str) -> str:
    name = value.strip()
    if not SAFE_BUNDLE_NAME.fullmatch(name):
        raise ValueError(f"{field} must match {SAFE_BUNDLE_NAME.pattern}")
    return name

def resolve_bundle_member(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise ValueError(f"invalid bundle member path: {relative!r}")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"bundle member escapes bundle root: {relative}") from exc
    return candidate

def parse_file_bindings(values: list[str], field: str) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"{field} binding must be NAME=PATH")
        name, raw_path = value.split("=", 1)
        name = safe_bundle_name(name, field)
        if name in result:
            raise ValueError(f"duplicate {field} binding: {name}")
        path = Path(raw_path).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"{field} file missing: {path}")
        result[name] = path
    return result

def load_json_mapping(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value

def write_canonical_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")

def create_bundle(
    ledger: Path,
    output: Path,
    repository_revision: str,
    *,
    evidence_files: dict[str, Path] | None = None,
    checkpoint_public_keys: dict[str, Path] | None = None,
    hmac_secrets: dict[str, str] | None = None,
    require_authenticated_verification: bool = False,
    anchor_output: Path | None = None,
) -> dict[str, Any]:
    revision = repository_revision.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40,64}", revision):
        raise ValueError("repository_revision must be a 40-64 character hexadecimal commit identifier")
    if not ledger.is_file():
        raise ValueError(f"ledger file missing: {ledger}")
    if output.exists():
        raise ValueError(f"bundle output already exists: {output}")
    if anchor_output is not None and anchor_output.exists():
        raise ValueError(f"anchor output already exists: {anchor_output}")

    evidence_files = evidence_files or {}
    checkpoint_public_keys = checkpoint_public_keys or {}
    hmac_secrets = hmac_secrets or {}
    events = read_ledger(ledger)
    if not events:
        raise ValueError("cannot create an audit bundle from an empty ledger")
    verification = verify_events(
        events,
        hmac_secrets=hmac_secrets,
        checkpoint_public_keys=checkpoint_public_keys,
        require_authenticated_verification=require_authenticated_verification,
        require_checkpoint_verification=True,
    )
    if verification["status"] != "PASS":
        raise ValueError("refusing to bundle invalid audit history: " + "; ".join(verification["errors"]))

    for key_id in checkpoint_public_keys:
        safe_bundle_name(key_id, "checkpoint key id")

    output.mkdir(parents=True)
    bundled_ledger = output / BUNDLE_LEDGER
    bundled_ledger.write_bytes(ledger.read_bytes())

    evidence_entries: list[dict[str, Any]] = []
    if evidence_files:
        (output / "evidence").mkdir()
    for name in sorted(evidence_files):
        source = evidence_files[name]
        target_rel = f"evidence/{name}"
        target = resolve_bundle_member(output, target_rel)
        target.write_bytes(source.read_bytes())
        evidence_entries.append({
            "name": name,
            "path": target_rel,
            "sha256": file_sha256(target),
            "bytes": target.stat().st_size,
        })

    public_key_entries: list[dict[str, Any]] = []
    if checkpoint_public_keys:
        (output / "public-keys").mkdir()
    for key_id in sorted(checkpoint_public_keys):
        source = checkpoint_public_keys[key_id]
        target_rel = f"public-keys/{key_id}.pem"
        target = resolve_bundle_member(output, target_rel)
        target.write_bytes(source.read_bytes())
        public_key_entries.append({
            "key_id": key_id,
            "path": target_rel,
            "sha256": file_sha256(target),
            "public_key_fingerprint": public_key_fingerprint(target),
            "bytes": target.stat().st_size,
        })

    manifest = {
        "version": 1,
        "bundle_type": BUNDLE_TYPE,
        "repository_revision": revision,
        "ledger": {
            "path": BUNDLE_LEDGER,
            "sha256": file_sha256(bundled_ledger),
            "events": verification["events"],
            "chain_head": verification["chain_head"],
            "authentication": verification["authentication"],
            "checkpoints": verification["checkpoints"],
        },
        "public_keys": public_key_entries,
        "evidence": evidence_entries,
        "authority": {
            "evidence_only": True,
            "approval_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "publication_authorized": False,
            "production_authorized": False,
        },
    }
    manifest_path = output / BUNDLE_MANIFEST
    write_canonical_json(manifest_path, manifest)
    anchor = {
        "version": 1,
        "bundle_type": BUNDLE_TYPE,
        "repository_revision": revision,
        "events": verification["events"],
        "chain_head": verification["chain_head"],
        "manifest_sha256": file_sha256(manifest_path),
    }
    anchor_path = output / BUNDLE_ANCHOR
    write_canonical_json(anchor_path, anchor)
    if anchor_output is not None:
        anchor_output.parent.mkdir(parents=True, exist_ok=True)
        anchor_output.write_bytes(anchor_path.read_bytes())
    return {
        "status": "BUNDLE_CREATED",
        "bundle": str(output),
        "repository_revision": revision,
        "events": verification["events"],
        "chain_head": verification["chain_head"],
        "manifest_sha256": anchor["manifest_sha256"],
        "evidence_files": len(evidence_entries),
        "public_keys": len(public_key_entries),
        "external_anchor_written": anchor_output is not None,
    }

def verify_bundle(
    bundle: Path,
    *,
    anchor_path: Path | None = None,
    hmac_secrets: dict[str, str] | None = None,
    require_authenticated_verification: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest_path = bundle / BUNDLE_MANIFEST
    selected_anchor = anchor_path or (bundle / BUNDLE_ANCHOR)
    if not manifest_path.is_file():
        return {"status": "FAIL", "errors": [f"missing {BUNDLE_MANIFEST}"]}
    if not selected_anchor.is_file():
        return {"status": "FAIL", "errors": [f"missing anchor: {selected_anchor}"]}

    manifest = load_json_mapping(manifest_path, BUNDLE_MANIFEST)
    anchor = load_json_mapping(selected_anchor, "anchor")
    if manifest.get("version") != 1 or manifest.get("bundle_type") != BUNDLE_TYPE:
        errors.append("unsupported bundle manifest")
    if anchor.get("version") != 1 or anchor.get("bundle_type") != BUNDLE_TYPE:
        errors.append("unsupported bundle anchor")
    manifest_digest = file_sha256(manifest_path)
    if anchor.get("manifest_sha256") != manifest_digest:
        errors.append("anchor manifest_sha256 mismatch")
    for field in ("repository_revision", "events", "chain_head"):
        expected = (manifest.get("ledger") or {}).get(field) if field in {"events", "chain_head"} else manifest.get(field)
        if anchor.get(field) != expected:
            errors.append(f"anchor {field} mismatch")

    ledger_meta = manifest.get("ledger") or {}
    ledger_rel = str(ledger_meta.get("path") or "")
    try:
        ledger_path = resolve_bundle_member(bundle, ledger_rel)
    except ValueError as exc:
        errors.append(str(exc))
        ledger_path = bundle / "__invalid_ledger__"
    if not ledger_path.is_file():
        errors.append("bundled ledger missing")
    elif ledger_meta.get("sha256") != file_sha256(ledger_path):
        errors.append("bundled ledger sha256 mismatch")

    checkpoint_keys: dict[str, Path] = {}
    seen_key_ids: set[str] = set()
    public_entries = manifest.get("public_keys") or []
    if not isinstance(public_entries, list):
        errors.append("public_keys must be a list")
        public_entries = []
    for item in public_entries:
        if not isinstance(item, dict):
            errors.append("public key entry must be an object")
            continue
        key_id = str(item.get("key_id") or "")
        if key_id in seen_key_ids:
            errors.append(f"duplicate public key id: {key_id}")
            continue
        seen_key_ids.add(key_id)
        try:
            safe_bundle_name(key_id, "checkpoint key id")
            key_path = resolve_bundle_member(bundle, str(item.get("path") or ""))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not key_path.is_file():
            errors.append(f"public key missing: {key_id}")
            continue
        if item.get("sha256") != file_sha256(key_path):
            errors.append(f"public key sha256 mismatch: {key_id}")
        if item.get("public_key_fingerprint") != public_key_fingerprint(key_path):
            errors.append(f"public key fingerprint mismatch: {key_id}")
        checkpoint_keys[key_id] = key_path

    seen_evidence: set[str] = set()
    evidence_entries = manifest.get("evidence") or []
    if not isinstance(evidence_entries, list):
        errors.append("evidence must be a list")
        evidence_entries = []
    for item in evidence_entries:
        if not isinstance(item, dict):
            errors.append("evidence entry must be an object")
            continue
        name = str(item.get("name") or "")
        if name in seen_evidence:
            errors.append(f"duplicate evidence name: {name}")
            continue
        seen_evidence.add(name)
        try:
            safe_bundle_name(name, "evidence name")
            evidence_path = resolve_bundle_member(bundle, str(item.get("path") or ""))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not evidence_path.is_file():
            errors.append(f"evidence file missing: {name}")
            continue
        if item.get("sha256") != file_sha256(evidence_path):
            errors.append(f"evidence sha256 mismatch: {name}")
        if item.get("bytes") != evidence_path.stat().st_size:
            errors.append(f"evidence size mismatch: {name}")

    ledger_verification: dict[str, Any] | None = None
    if ledger_path.is_file():
        try:
            ledger_verification = verify_events(
                read_ledger(ledger_path),
                hmac_secrets=hmac_secrets or {},
                checkpoint_public_keys=checkpoint_keys,
                require_authenticated_verification=require_authenticated_verification,
                require_checkpoint_verification=True,
                expected_chain_head=str(ledger_meta.get("chain_head") or ""),
                expected_events=int(ledger_meta.get("events")),
            )
            if ledger_verification["status"] != "PASS":
                errors.extend(ledger_verification["errors"])
            if ledger_meta.get("authentication") != ledger_verification.get("authentication"):
                errors.append("ledger authentication summary mismatch")
            if ledger_meta.get("checkpoints") != ledger_verification.get("checkpoints"):
                errors.append("ledger checkpoint summary mismatch")
        except (OSError, ValueError, TypeError, RuntimeError, json.JSONDecodeError) as exc:
            errors.append(f"bundled ledger verification failed: {exc}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "repository_revision": manifest.get("repository_revision"),
        "events": (ledger_verification or {}).get("events"),
        "chain_head": (ledger_verification or {}).get("chain_head"),
        "manifest_sha256": manifest_digest,
        "anchor_source": "external" if anchor_path is not None else "bundle",
        "evidence_files": len(evidence_entries),
        "public_keys": len(public_entries),
        "errors": errors,
    }

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
    bundle_create = sub.add_parser("bundle-create")
    bundle_create.add_argument("--ledger", required=True)
    bundle_create.add_argument("--output", required=True)
    bundle_create.add_argument("--repository-revision", required=True)
    bundle_create.add_argument("--evidence", action="append", default=[], metavar="NAME=PATH")
    bundle_create.add_argument("--checkpoint-public-key", action="append", default=[], metavar="KEY_ID=PATH")
    bundle_create.add_argument("--hmac", action="append", default=[], metavar="KEY_ID=ENV_NAME")
    bundle_create.add_argument("--require-auth-verification", action="store_true")
    bundle_create.add_argument("--anchor-output")
    bundle_verify = sub.add_parser("bundle-verify")
    bundle_verify.add_argument("--bundle", required=True)
    bundle_verify.add_argument("--anchor")
    bundle_verify.add_argument("--hmac", action="append", default=[], metavar="KEY_ID=ENV_NAME")
    bundle_verify.add_argument("--require-auth-verification", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "bundle-create":
            doc = create_bundle(
                Path(args.ledger).expanduser().resolve(),
                Path(args.output).expanduser().resolve(),
                args.repository_revision,
                evidence_files=parse_file_bindings(args.evidence, "evidence"),
                checkpoint_public_keys=parse_public_keys(args.checkpoint_public_key),
                hmac_secrets=parse_key_bindings(args.hmac),
                require_authenticated_verification=args.require_auth_verification,
                anchor_output=Path(args.anchor_output).expanduser().resolve() if args.anchor_output else None,
            )
            emit(doc)
            return 0
        if args.command == "bundle-verify":
            result = verify_bundle(
                Path(args.bundle).expanduser().resolve(),
                anchor_path=Path(args.anchor).expanduser().resolve() if args.anchor else None,
                hmac_secrets=parse_key_bindings(args.hmac),
                require_authenticated_verification=args.require_auth_verification,
            )
            emit(result)
            return 0 if result["status"] == "PASS" else 2
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
