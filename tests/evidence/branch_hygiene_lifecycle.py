#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "branch_hygiene.py"


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
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "base")
        git(repo, "branch", "-M", "main")
        git(repo, "branch", "feature/merged")
        git(repo, "branch", "feature/retrieval-embedding-trial")
        git(repo, "checkout", "-qb", "feature/pending")
        (repo / "pending.txt").write_text("pending\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "pending")
        git(repo, "checkout", "-q", "main")

        config = repo / "branch-lifecycle.yaml"
        config.write_text(
            """version: 1
default_branch: main
persistent_exact: [main, feature/retrieval-embedding-trial]
persistent_patterns: []
ephemeral_patterns: [feature/*, release/*]
deletion:
  mode: report_only
  require_integrated_into_default: true
  preserve_unclassified: true
""",
            encoding="utf-8",
        )
        proc = subprocess.run(
            ["python3", str(SCRIPT), "--config", str(config), "--target", "main"],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        payload = yaml.safe_load(proc.stdout)
        rows = {row["branch"]: row for row in payload["branches"]}
        assert rows["feature/merged"]["deletion_candidate"] is True
        assert rows["feature/pending"]["deletion_candidate"] is False
        assert rows["feature/retrieval-embedding-trial"]["lifecycle"] == "PERSISTENT"
        assert payload["authority"]["branch_deletion_authorized"] is False

    print("branch hygiene lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
