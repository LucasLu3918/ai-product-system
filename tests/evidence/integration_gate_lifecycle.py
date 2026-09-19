#!/usr/bin/env python3
from __future__ import annotations

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
            "checks": [
                {"id": "syntax", "category": "lint", "required": True, "argv": ["python3", "-m", "py_compile", "app.py"]},
                {"id": "tests", "category": "test", "required": True, "argv": ["python3", "-c", "import app; assert app.value == 2"]},
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
        assert payload["candidate"]["base_sha"] == base
        assert payload["candidate"]["base_tip_sha"] == base
        assert payload["candidate"]["head_sha"] == head
        assert payload["candidate"]["changed_files"] == ["app.py"]
        assert payload["authority"]["merge_authorized"] is False

        git(repo, "branch", "-f", "base-tip", head)
        stale_base = subprocess.run(
            ["python3", str(SCRIPT), "--profile", str(profile_path), "--base", base, "--head", head, "--base-tip", "base-tip", "--output", str(repo / "stale-base.yaml")],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert stale_base.returncode == 2
        assert "candidate base is stale" in stale_base.stdout
        git(repo, "branch", "-f", "base-tip", base)

        stale = subprocess.run(
            ["python3", str(SCRIPT), "--profile", str(profile_path), "--base", base, "--head", base, "--output", str(repo / "stale.yaml")],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert stale.returncode == 2
        assert "candidate checkout mismatch" in stale.stdout

        failing = dict(profile)
        failing["checks"] = list(profile["checks"]) + [
            {"id": "failure", "category": "test", "required": True, "argv": ["python3", "-c", "raise SystemExit(7)"]}
        ]
        bad_path = repo / "bad.yaml"
        bad_path.write_text(yaml.safe_dump(failing, sort_keys=False), encoding="utf-8")
        bad_report = repo / "bad-report.json"
        bad = subprocess.run(
            ["python3", str(SCRIPT), "--profile", str(bad_path), "--base", base, "--head", head, "--output", str(bad_report), "--format", "json"],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert bad.returncode == 1
        bad_payload = json.loads(bad_report.read_text(encoding="utf-8"))
        assert bad_payload["status"] == "FAIL"
        assert bad_payload["blockers"] == ["failure"]

    print("integration gate lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
