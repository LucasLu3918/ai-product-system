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


def validate(payload: dict) -> None:
    rows = {row["branch"]: row for row in payload["branches"]}
    assert rows["feature/merged"]["deletion_candidate"] is True
    assert rows["feature/squashed"]["deletion_candidate"] is True
    assert rows["feature/pending"]["deletion_candidate"] is False
    assert rows["feature/retrieval-embedding-trial"]["lifecycle"] == "PERSISTENT"
    assert payload["authority"]["branch_deletion_authorized"] is False
    assert payload["authority"]["human_authority_preserved"] is True


def remote_exists(repo: Path, name: str) -> bool:
    proc = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", f"refs/heads/{name}"],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    return proc.returncode == 0


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo = root / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "AIPS Test")
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "base")
        git(repo, "branch", "-M", "main")

        git(repo, "checkout", "-qb", "feature/squashed")
        (repo / "squashed-a.txt").write_text("a\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "squashed a")
        (repo / "squashed-b.txt").write_text("b\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "squashed b")
        squashed_sha = git(repo, "rev-parse", "HEAD")
        git(repo, "checkout", "-q", "main")
        git(repo, "merge", "--squash", "feature/squashed")
        git(repo, "commit", "-qm", "squash feature")

        git(repo, "branch", "feature/merged")
        merged_sha = git(repo, "rev-parse", "feature/merged")
        git(repo, "branch", "feature/retrieval-embedding-trial")
        git(repo, "checkout", "-qb", "feature/pending")
        (repo / "pending.txt").write_text("pending\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "pending")
        pending_sha = git(repo, "rev-parse", "HEAD")
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

        local = subprocess.run(
            ["python3", str(SCRIPT), "--config", str(config), "--target", "main"],
            cwd=repo, text=True, capture_output=True,
        )
        assert local.returncode == 0, local.stdout + local.stderr
        validate(yaml.safe_load(local.stdout))

        remote = root / "remote.git"
        git(root, "init", "--bare", "-q", str(remote))
        git(repo, "remote", "add", "origin", str(remote))
        git(repo, "push", "-q", "origin", "--all")
        git(repo, "fetch", "-q", "origin", "+refs/heads/*:refs/remotes/origin/*")

        remote_run = subprocess.run(
            ["python3", str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin"],
            cwd=repo, text=True, capture_output=True,
        )
        assert remote_run.returncode == 0, remote_run.stdout + remote_run.stderr
        validate(yaml.safe_load(remote_run.stdout))

        blocked_manifest = repo / "blocked-cleanup.yaml"
        blocked_manifest.write_text(yaml.safe_dump({
            "version": 1,
            "cleanup_id": "blocked-test",
            "baseline_main_sha": git(repo, "rev-parse", "main"),
            "authorization": {
                "type": "explicit_user_request",
                "approved_by": "test-maintainer",
                "approved_at": "2026-09-21",
                "scope": "exact_manifest_only",
                "one_time": True,
            },
            "branches": [
                {"branch": "feature/merged", "expected_sha": merged_sha, "merged_pr": 1},
                {"branch": "feature/pending", "expected_sha": pending_sha, "merged_pr": 2},
            ],
        }, sort_keys=False), encoding="utf-8")
        blocked = subprocess.run(
            ["python3", str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin",
             "--apply-cleanup", str(blocked_manifest)],
            cwd=repo, text=True, capture_output=True,
        )
        assert blocked.returncode != 0
        assert remote_exists(repo, "feature/merged"), "batch preflight must prevent partial deletion"

        cleanup_manifest = repo / "cleanup.yaml"
        cleanup_manifest.write_text(yaml.safe_dump({
            "version": 1,
            "cleanup_id": "approved-test",
            "baseline_main_sha": git(repo, "rev-parse", "main"),
            "authorization": {
                "type": "explicit_user_request",
                "approved_by": "test-maintainer",
                "approved_at": "2026-09-21",
                "scope": "exact_manifest_only",
                "one_time": True,
            },
            "branches": [
                {"branch": "feature/merged", "expected_sha": merged_sha, "merged_pr": 1},
                {"branch": "feature/squashed", "expected_sha": squashed_sha, "merged_pr": 2},
            ],
        }, sort_keys=False), encoding="utf-8")
        cleanup = subprocess.run(
            ["python3", str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin",
             "--apply-cleanup", str(cleanup_manifest)],
            cwd=repo, text=True, capture_output=True,
        )
        assert cleanup.returncode == 0, cleanup.stdout + cleanup.stderr
        cleanup_doc = yaml.safe_load(cleanup.stdout)
        assert cleanup_doc["summary"]["deleted"] == 2
        assert cleanup_doc["authority"]["authorization_scope"] == "exact_manifest_only"
        assert not remote_exists(repo, "feature/merged")
        assert not remote_exists(repo, "feature/squashed")
        assert remote_exists(repo, "feature/pending")
        assert remote_exists(repo, "feature/retrieval-embedding-trial")

    print("branch hygiene lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
