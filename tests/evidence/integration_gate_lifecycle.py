#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from review_evidence import canonical_hash

SCRIPT = ROOT / "scripts" / "integration_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("integration_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return proc.stdout.strip()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    gate = load_gate()
    valid_count = gate.run_check({
        "id": "test-count-valid", "category": "test", "applies": True,
        "argv": [sys.executable, "-c", "print('Ran 5 tests in 0.01s')"],
        "expected_test_count": 5,
    })
    assert valid_count["status"] == "PASS"
    empty_count = gate.run_check({
        "id": "test-count-empty", "category": "test", "applies": True,
        "argv": [sys.executable, "-c", "print('Ran 0 tests in 0.01s')"],
        "expected_test_count": 5,
    })
    assert empty_count["status"] == "FAIL"
    assert empty_count["reason"] == "expected_5_tests_collected_got_0"
    unreported_count = gate.run_check({
        "id": "test-count-unreported", "category": "test", "applies": True,
        "argv": [sys.executable, "-c", "print('command exited successfully')"],
        "expected_test_count": 5,
    })
    assert unreported_count["status"] == "FAIL"
    assert unreported_count["reason"] == "expected_test_count_missing_from_runner_output"

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "AIPS Test")
        (repo / "app.py").write_text("value: int = 1\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "base")
        base = git(repo, "rev-parse", "HEAD")
        (repo / "app.py").write_text("value: int = 2\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "candidate")
        head = git(repo, "rev-parse", "HEAD")

        profile = {
            "version": 1,
            "profile_id": "fixture",
            "matrix_required": False,
            "matrix_required_change_classes": ["large", "core"],
            "matrix_required_paths": [],
            "checks": [
                {"id": "syntax", "category": "lint", "required": True, "argv": [sys.executable, "-m", "py_compile", "app.py"]},
                {"id": "env", "category": "test", "required": True, "env": {"AIPS_FIXTURE": "1"}, "argv": [sys.executable, "-c", "import os; assert os.environ['AIPS_FIXTURE'] == '1'"]},
            ],
        }
        profile_path = repo / "profile.yaml"
        profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
        git(repo, "branch", "base-tip", base)

        report = repo / "report.json"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(profile_path), "--base", base, "--head", head, "--base-tip", "base-tip", "--output", str(report), "--format", "json"],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        payload = json.loads(report.read_text(encoding="utf-8"))
        assert payload["status"] == "PASS"
        assert payload["candidate"]["matrix_required"] is False
        assert payload["candidate"]["change_class"] == "standard"

        sensitive_profile = dict(profile)
        sensitive_profile["checks"] = [{
            "id": "failing-secret-output", "category": "test", "required": True,
            "argv": [sys.executable, "-c", "print('token=fixture-secret'); raise SystemExit(1)"],
        }]
        sensitive_path = repo / "sensitive-profile.yaml"
        sensitive_path.write_text(yaml.safe_dump(sensitive_profile), encoding="utf-8")
        safe_report = repo / "safe-report.json"
        safe = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(sensitive_path),
             "--base", base, "--head", head, "--omit-output-tail",
             "--output", str(safe_report), "--format", "json"],
            cwd=repo, text=True, capture_output=True,
        )
        assert safe.returncode == 1, safe.stdout + safe.stderr
        assert "fixture-secret" not in safe.stdout + safe_report.read_text(encoding="utf-8")
        safe_check = json.loads(safe_report.read_text(encoding="utf-8"))["checks"][0]
        assert safe_check["status"] == "FAIL"
        assert "output_tail" not in safe_check
        assert len(safe_check["output_sha256"]) == 64

        conditional = dict(profile)
        conditional["matrix_required_paths"] = ["app.py"]
        conditional_path = repo / "conditional.yaml"
        conditional_path.write_text(yaml.safe_dump(conditional, sort_keys=False), encoding="utf-8")
        missing = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(conditional_path), "--base", base, "--head", head],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert missing.returncode == 2
        assert "requires Core Change Test Matrix" in missing.stdout

        matrix = {
            "version": 1,
            "candidate": {"base_sha": base, "changed_files_hash": canonical_hash(["app.py"])},
            "actual_diff_reconciled": True,
            "blockers": [],
            "status": "PASS",
        }
        matrix_path = repo / "matrix.yaml"
        matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False), encoding="utf-8")
        bound = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(conditional_path), "--base", base, "--head", head, "--matrix", str(matrix_path)],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert bound.returncode == 0, bound.stdout + bound.stderr

        review_disabled_matrix = {
            **matrix,
            "status": "PASS",
            "review_evidence": {"required": False, "path": "unused.yaml"},
        }
        matrix_path.write_text(yaml.safe_dump(review_disabled_matrix, sort_keys=False), encoding="utf-8")
        disabled_review = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(conditional_path), "--base", base,
             "--head", head, "--base-tip", "base-tip", "--matrix", str(matrix_path), "--format", "json"],
            cwd=repo, text=True, capture_output=True,
        )
        assert disabled_review.returncode == 0, disabled_review.stdout + disabled_review.stderr
        disabled_payload = json.loads(disabled_review.stdout)
        assert disabled_payload["status"] == "PASS"
        assert disabled_payload["review_evidence"]["status"] == "NOT_REQUIRED"

        review_required_matrix = {
            **matrix,
            "status": "PASS",
            "review_evidence": {"required": True, "path": "unused.yaml"},
        }
        matrix_path.write_text(yaml.safe_dump(review_required_matrix, sort_keys=False), encoding="utf-8")
        evidence = {
            "version": 1,
            "mode": "INDEPENDENT_REVIEW",
            "review_of_task": "implementation",
            "candidate": {
                "base_sha": base,
                "head_sha": head,
                "changed_files_hash": canonical_hash(["app.py"]),
            },
            "packet": {"fingerprint": "sha256:" + "a" * 64, "source_classes": ["diff"]},
            "context_policy": {
                "inheritance": "none", "packet_fingerprint": "sha256:" + "a" * 64,
                "allowed_classes": ["diff"],
                "denied_classes": ["implementation_transcript", "private_reasoning", "scratchpad", "raw_model_trace"],
            },
            "permissions": {"read_only": True, "write_set": []},
            "implementer_execution_id": "impl-1",
            "reviewer_execution_id": "review-1",
            "runtime_attestation": {
                "execution_identity": "VERIFIED", "context_isolation": "VERIFIED",
                "read_only_authority": "VERIFIED", "runtime": "fixture",
                "receipt_ref": "fixture://receipt", "receipt_sha256": "sha256:" + "b" * 64,
                "issuer_key_id": "fixture-key", "signature_algorithm": "ed25519", "signature_b64": "AA==",
                "packet_fingerprint": "sha256:" + "a" * 64,
            },
            "unresolved_blocking_findings": 0,
        }
        evidence_path = Path(td) / "review-evidence.yaml"
        evidence_path.write_text(yaml.safe_dump(evidence, sort_keys=False), encoding="utf-8")
        accepted = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(conditional_path), "--base", base, "--head", head,
             "--base-tip", "base-tip", "--matrix", str(matrix_path), "--review-evidence", str(evidence_path),
             "--format", "json"], cwd=repo, text=True, capture_output=True,
        )
        assert accepted.returncode == 1, accepted.stdout + accepted.stderr
        accepted_payload = json.loads(accepted.stdout)
        assert accepted_payload["review_evidence"]["status"] == "UNVERIFIED"
        assert accepted_payload["review_evidence"]["reason_codes"] == ["trusted_runtime_attestation_verifier_unavailable"]

        missing_review = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(conditional_path), "--base", base, "--head", head,
             "--base-tip", "base-tip", "--matrix", str(matrix_path), "--format", "json"],
            cwd=repo, text=True, capture_output=True,
        )
        assert missing_review.returncode == 1
        assert "independent-review-evidence" in json.loads(missing_review.stdout)["blockers"]

        stale_evidence = {**evidence, "candidate": {**evidence["candidate"], "head_sha": base}}
        evidence_path.write_text(yaml.safe_dump(stale_evidence, sort_keys=False), encoding="utf-8")
        rejected_review = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(conditional_path), "--base", base, "--head", head,
             "--base-tip", "base-tip", "--matrix", str(matrix_path), "--review-evidence", str(evidence_path),
             "--format", "json"], cwd=repo, text=True, capture_output=True,
        )
        assert rejected_review.returncode == 1
        assert json.loads(rejected_review.stdout)["review_evidence"]["status"] == "STALE"

        wrong = dict(matrix)
        wrong["candidate"] = {"base_sha": base, "changed_files_hash": "wrong"}
        matrix_path.write_text(yaml.safe_dump(wrong, sort_keys=False), encoding="utf-8")
        stale_matrix = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(conditional_path), "--base", base, "--head", head, "--matrix", str(matrix_path)],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert stale_matrix.returncode == 2
        assert "changed_files_hash does not match" in stale_matrix.stdout

        git(repo, "branch", "-f", "base-tip", head)
        stale_base = subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", str(profile_path), "--base", base, "--head", head, "--base-tip", "base-tip"],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert stale_base.returncode == 2
        assert "candidate base is stale" in stale_base.stdout

    print("integration gate lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
