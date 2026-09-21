#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "scripts" / "governance_audit.py"
RETENTION = ROOT / "scripts" / "governance_audit_retention.py"
POLICY = ROOT / "config" / "governance-audit-retention.yaml"


def run(script: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = dict(os.environ)
    if env:
        merged.update(env)
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, env=merged, timeout=45)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def event(path: Path, event_type: str, occurred_at: str) -> None:
    path.write_text(json.dumps({
        "version": 1,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "actor": {"type": "system", "id": "retention-test"},
        "authority": {"source": "test", "approval_id": "approval-retention"},
        "binding": {
            "approval_scope_fingerprint": "sha256:" + ("1" * 64),
            "candidate_commit": "a" * 40,
            "branch": "feature/test",
            "operation": event_type.lower(),
            "result": "PASS",
            "evidence_digests": ["sha256:" + ("2" * 64)],
        },
    }), encoding="utf-8")


def descriptor(path: Path, bundle_id: str, bundle: Path, anchor: Path | None, subject: str,
               sal: int, retained_on: str, legal_hold: bool = False) -> None:
    path.write_text(yaml.safe_dump({
        "version": 1,
        "bundle_id": bundle_id,
        "subject": {"type": "release", "id": subject},
        "sal": sal,
        "retained_on": retained_on,
        "legal_hold": legal_hold,
        "bundle_path": str(bundle),
        "anchor_path": str(anchor) if anchor else None,
    }, sort_keys=False), encoding="utf-8")


def create_plain_bundle(root: Path, name: str, revision: str) -> tuple[Path, Path]:
    event_file = root / f"{name}-event.json"
    ledger = root / f"{name}.jsonl"
    event(event_file, "RELEASE_READINESS_READY", "2026-09-21T00:00:00Z")
    require(run(AUDIT, "append", "--ledger", str(ledger), "--event", str(event_file)).returncode == 0,
            f"{name} ledger append failed")
    bundle = root / f"{name}-bundle"
    anchor = root / f"{name}-anchor.json"
    made = run(AUDIT, "bundle-create", "--ledger", str(ledger), "--output", str(bundle),
               "--repository-revision", revision, "--anchor-output", str(anchor))
    require(made.returncode == 0, f"{name} bundle create failed: {made.stdout} {made.stderr}")
    return bundle, anchor


def create_signed_bundle(root: Path, name: str, revision: str, key_id: str,
                         private_key: Path, public_key: Path) -> tuple[Path, Path]:
    event_file = root / f"{name}-event.json"
    ledger = root / f"{name}.jsonl"
    event(event_file, "PRODUCTION_VERIFIED", "2026-09-21T00:01:00Z")
    added = run(AUDIT, "append", "--ledger", str(ledger), "--event", str(event_file),
                "--checkpoint-private-key", str(private_key),
                "--checkpoint-public-key", str(public_key),
                "--checkpoint-key-id", key_id)
    require(added.returncode == 0, f"{name} signed append failed: {added.stdout} {added.stderr}")
    bundle = root / f"{name}-bundle"
    anchor = root / f"{name}-anchor.json"
    made = run(AUDIT, "bundle-create", "--ledger", str(ledger), "--output", str(bundle),
               "--repository-revision", revision,
               "--checkpoint-public-key", f"{key_id}={public_key}",
               "--anchor-output", str(anchor))
    require(made.returncode == 0, f"{name} signed bundle create failed: {made.stdout} {made.stderr}")
    return bundle, anchor


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        old_bundle, old_anchor = create_plain_bundle(root, "old", "a" * 40)
        hold_bundle, hold_anchor = create_plain_bundle(root, "hold", "b" * 40)
        old_desc = root / "old.yaml"
        hold_desc = root / "hold.yaml"
        descriptor(old_desc, "release-v1", old_bundle, old_anchor, "v1.0.0", 2, "2020-01-01")
        descriptor(hold_desc, "release-v2", hold_bundle, hold_anchor, "v2.0.0", 3, "2020-01-01", True)

        entries = [old_desc, hold_desc]
        signed_descriptors: list[Path] = []
        if shutil.which("openssl"):
            key1 = root / "key1.pem"; pub1 = root / "key1.pub.pem"
            key2 = root / "key2.pem"; pub2 = root / "key2.pub.pem"
            subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key1)], check=True, timeout=15)
            subprocess.run(["openssl", "pkey", "-in", str(key1), "-pubout", "-out", str(pub1)], check=True, timeout=15)
            subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key2)], check=True, timeout=15)
            subprocess.run(["openssl", "pkey", "-in", str(key2), "-pubout", "-out", str(pub2)], check=True, timeout=15)

            signed1, signed_anchor1 = create_signed_bundle(root, "signed1", "c" * 40, "release-key-2026q3", key1, pub1)
            signed2, signed_anchor2 = create_signed_bundle(root, "signed2", "d" * 40, "release-key-2026q4", key2, pub2)
            desc1 = root / "signed1.yaml"; desc2 = root / "signed2.yaml"
            descriptor(desc1, "release-v3", signed1, signed_anchor1, "v3.0.0", 4, "2026-07-01")
            descriptor(desc2, "release-v4", signed2, signed_anchor2, "v4.0.0", 4, "2026-09-01")
            entries.extend([desc1, desc2]); signed_descriptors.extend([desc1, desc2])

        catalog = root / "CATALOG.json"
        args = ["catalog-build", "--policy", str(POLICY), "--output", str(catalog)]
        for item in entries:
            args.extend(["--entry", str(item)])
        built = run(RETENTION, *args)
        require(built.returncode == 0, f"catalog build failed: {built.stdout} {built.stderr}")
        require(run(RETENTION, "catalog-verify", "--policy", str(POLICY), "--catalog", str(catalog)).returncode == 0,
                "catalog verify failed")

        catalog_text = catalog.read_text(encoding="utf-8")
        require(str(root) not in catalog_text, "catalog leaked source absolute path")
        catalog_doc = json.loads(catalog_text)
        require(catalog_doc["authority"]["deletion_authorized"] is False, "catalog must not authorize deletion")

        found = run(RETENTION, "catalog-find", "--policy", str(POLICY), "--catalog", str(catalog),
                    "--repository-revision", "a" * 40)
        require(found.returncode == 0 and json.loads(found.stdout)["count"] == 1,
                "catalog revision discovery failed")

        plan = run(RETENTION, "retention-plan", "--policy", str(POLICY), "--catalog", str(catalog),
                   "--as-of", "2026-09-21")
        require(plan.returncode == 0, f"retention plan failed: {plan.stdout} {plan.stderr}")
        plan_doc = json.loads(plan.stdout)
        actions = {item["bundle_id"]: item for item in plan_doc["actions"]}
        require(actions["release-v1"]["state"] == "REVIEW_DUE", "expired SAL2 bundle must be review due")
        require(actions["release-v1"]["proposed_action"] == "HUMAN_REVIEW_FOR_COMPACTION",
                "review due bundle must request Human review")
        require(actions["release-v1"]["deletion_authorized"] is False, "retention plan must not authorize deletion")
        require(actions["release-v1"]["minimal_record"]["record_fingerprint"].startswith("sha256:"),
                "minimal digest record missing fingerprint")
        require(actions["release-v2"]["state"] == "HOLD_FULL", "legal hold must override retention age")

        tampered = json.loads(catalog_text)
        tampered["entries"][0]["chain_head"] = "sha256:" + ("f" * 64)
        catalog.write_text(json.dumps(tampered), encoding="utf-8")
        require(run(RETENTION, "catalog-verify", "--policy", str(POLICY), "--catalog", str(catalog)).returncode != 0,
                "tampered catalog must fail fingerprint verification")
        catalog.write_text(catalog_text, encoding="utf-8")

        if signed_descriptors:
            registry = catalog_doc["checkpoint_key_registry"]
            require([item["key_id"] for item in registry] == ["release-key-2026q3", "release-key-2026q4"],
                    "key rotation registry must preserve distinct key ids")

            other_private = root / "other.pem"; other_public = root / "other.pub.pem"
            subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(other_private)], check=True, timeout=15)
            subprocess.run(["openssl", "pkey", "-in", str(other_private), "-pubout", "-out", str(other_public)], check=True, timeout=15)
            dup_bundle, dup_anchor = create_signed_bundle(root, "dup", "e" * 40, "release-key-2026q3",
                                                          other_private, other_public)
            dup_desc = root / "dup.yaml"
            descriptor(dup_desc, "release-v5", dup_bundle, dup_anchor, "v5.0.0", 4, "2026-09-10")
            bad_catalog = root / "BAD-CATALOG.json"
            bad = run(RETENTION, "catalog-build", "--policy", str(POLICY), "--output", str(bad_catalog),
                      "--entry", str(signed_descriptors[0]), "--entry", str(dup_desc))
            require(bad.returncode != 0 and "checkpoint key id fingerprint changed" in bad.stdout,
                    "same key id with a different fingerprint must fail closed")

    print("governance audit retention lifecycle PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
