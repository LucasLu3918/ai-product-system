#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "integration_gate.py"


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return proc.stdout.strip()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
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
                {"id": "syntax", "category": "lint", "required": True, "argv": ["python3", "-m", "py_compile", "app.py"]},
                {"id": "env", "category": "test", "required": True, "env": {"AIPS_FIXTURE": "1"}, "argv": ["python3", "-c", "import os; assert os.environ['AIPS_FIXTURE'] == '1'"]},
            ],
        }
        profile_path = repo / "profile.yaml"
        profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
        git(repo, "branch", "base-tip", base)

        report = repo / "report.json"
        proc = subprocess.run(
            ["python3", str(SCRIPT), "--profile", str(profile_path), "--base", base, "--head", head, "--base-tip", "base-tip", "--output", str(report), "--format", "json"],
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
            "argv": ["python3", "-c", "print('token=fixture-secret'); raise SystemExit(1)"],
        }]
        sensitive_path = repo / "sensitive-profile.yaml"
        sensitive_path.write_text(yaml.safe_dump(sensitive_profile), encoding="utf-8")
        safe_report = repo / "safe-report.json"
        safe = subprocess.run(
            ["python3", str(SCRIPT), "--profile", str(sensitive_path),
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
            ["python3", str(SCRIPT), "--profile", str(conditional_path), "--base", base, "--head", head],
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
            ["python3", str(SCRIPT), "--profile", str(conditional_path), "--base", base, "--head", head, "--matrix", str(matrix_path)],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert bound.returncode == 0, bound.stdout + bound.stderr

        wrong = dict(matrix)
        wrong["candidate"] = {"base_sha": base, "changed_files_hash": "wrong"}
        matrix_path.write_text(yaml.safe_dump(wrong, sort_keys=False), encoding="utf-8")
        stale_matrix = subprocess.run(
            ["python3", str(SCRIPT), "--profile", str(conditional_path), "--base", base, "--head", head, "--matrix", str(matrix_path)],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert stale_matrix.returncode == 2
        assert "changed_files_hash does not match" in stale_matrix.stdout

        git(repo, "branch", "-f", "base-tip", head)
        stale_base = subprocess.run(
            ["python3", str(SCRIPT), "--profile", str(profile_path), "--base", base, "--head", head, "--base-tip", "base-tip"],
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
