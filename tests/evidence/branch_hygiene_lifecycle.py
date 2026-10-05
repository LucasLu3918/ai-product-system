#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "branch_hygiene.py"
sys.path.insert(0, str(ROOT / "scripts"))
from branch_hygiene import BranchHygieneError, classify, validate_proposal


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return proc.stdout.strip()


def validate(payload: dict) -> None:
    rows = {row["branch"]: row for row in payload["branches"]}
    assert rows["feature/merged"]["recommended_action"] == "REVIEW_FOR_CLEANUP"
    assert rows["feature/squashed"]["recommended_action"] == "REVIEW_FOR_CLEANUP"
    assert rows["feature/pending"]["recommended_action"] == "PRESERVE"
    assert {"current_sha", "merged_pr", "merged_status", "age_days", "integrated_into_target"}.issubset(rows["feature/merged"])
    assert rows["feature/retrieval-embedding-trial"]["lifecycle"] == "PERSISTENT"
    assert payload["authority"]["branch_deletion_authorized"] is False
    assert payload["authority"]["human_authority_preserved"] is True
    proposal = payload["cleanup_proposal"]
    assert proposal["authorization"]["authorized"] is False
    assert proposal["proposal_fingerprint"].startswith("sha256:")
    validate_proposal(proposal)


def remote_exists(repo: Path, name: str) -> bool:
    proc = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", f"refs/heads/{name}"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
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
        git(repo, "checkout", "-qb", "feature/pr-evidence")
        (repo / "pr-only.txt").write_text("provider evidence\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "pr evidence fixture")
        pr_evidence_sha = git(repo, "rev-parse", "HEAD")
        git(repo, "checkout", "-q", "main")

        config = repo / "branch-lifecycle.yaml"
        config_data = """version: 1
default_branch: main
persistent_exact: [main, feature/retrieval-embedding-trial]
persistent_patterns: []
ephemeral_patterns: [feat/*, feature/*, fix/*, ci/*, chore/*, perf/*, ops/*, release/*]
deletion:
  mode: report_only
  require_integrated_into_default: true
  preserve_unclassified: true
"""
        config.write_text(config_data, encoding="utf-8")
        parsed_config = yaml.safe_load(config_data)
        for prefix in ("feat/x", "feature/x", "fix/x", "ci/x", "chore/x", "perf/x", "ops/x", "release/x"):
            assert classify(prefix, parsed_config) == "EPHEMERAL", prefix
        assert classify("customer/keep-forever", parsed_config) == "UNCLASSIFIED"

        local = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(config), "--target", "main"],
            cwd=repo, text=True, capture_output=True,
            check=False,
        )
        assert local.returncode == 0, local.stdout + local.stderr
        validate(yaml.safe_load(local.stdout))

        prs = [
            {"number": 21, "headRefName": "feature/merged", "headRefOid": merged_sha, "baseRefName": "main", "state": "CLOSED", "mergedAt": "2026-09-21T00:00:00Z", "closedAt": "2026-09-21T00:00:00Z"},
            {"number": 22, "headRefName": "feature/pending", "headRefOid": pending_sha, "baseRefName": "main", "state": "OPEN", "mergedAt": None, "closedAt": None},
        ]
        pr_fixture = repo / "pull-requests.json"
        pr_fixture.write_text(json.dumps(prs), encoding="utf-8")
        dated = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(config), "--target", "main", "--pull-requests", str(pr_fixture), "--generated-at", "2026-10-01T00:00:00Z"],
            cwd=repo, text=True, capture_output=True,
            check=False,
        )
        assert dated.returncode == 0, dated.stdout + dated.stderr
        dated_report = yaml.safe_load(dated.stdout)
        dated_rows = {row["branch"]: row for row in dated_report["branches"]}
        assert dated_rows["feature/merged"]["merged_pr"] == 21
        assert dated_rows["feature/merged"]["merged_status"] == "MERGED"
        assert dated_rows["feature/pending"]["merged_status"] == "OPEN"
        assert dated_rows["feature/merged"]["age_days"] >= 0
        assert dated_report["authority"]["branch_deletion_authorized"] is False
        proposal = dated_report["cleanup_proposal"]
        assert proposal["generated_against_main_sha"] == git(repo, "rev-parse", "main")
        assert proposal["branches"][0]["merged_at"] == "2026-09-21T00:00:00Z"
        validate_proposal(
            proposal,
            current_main_sha=git(repo, "rev-parse", "main"),
            current_branch_shas={"feature/merged": merged_sha},
        )
        try:
            validate_proposal(proposal, current_main_sha="0" * 40)
        except BranchHygieneError:
            pass
        else:
            raise AssertionError("moved main baseline must invalidate a cleanup proposal")
        stale_proposal = json.loads(json.dumps(proposal))
        stale_proposal["branches"][0]["expected_sha"] = "0" * 40
        try:
            validate_proposal(stale_proposal)
        except BranchHygieneError:
            pass
        else:
            raise AssertionError("edited proposal content must fail fingerprint validation")

        remote = root / "remote.git"
        git(root, "init", "--bare", "-q", str(remote))
        git(repo, "remote", "add", "origin", str(remote))
        git(repo, "branch", "feature/partial-one", "main")
        partial_one_sha = git(repo, "rev-parse", "feature/partial-one")
        git(repo, "branch", "feature/partial-two", "main")
        partial_two_sha = git(repo, "rev-parse", "feature/partial-two")
        git(repo, "push", "-q", "origin", "--all")
        git(repo, "fetch", "-q", "origin", "+refs/heads/*:refs/remotes/origin/*")

        remote_run = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin"],
            cwd=repo, text=True, capture_output=True,
            check=False,
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
            [sys.executable, str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin",
             "--apply-cleanup", str(blocked_manifest)],
            cwd=repo, text=True, capture_output=True, check=False,
        )
        assert blocked.returncode != 0
        assert remote_exists(repo, "feature/merged"), "batch preflight must prevent partial deletion"

        fake_bin = root / "fake-bin"
        fake_bin.mkdir()
        fake_gh = fake_bin / "gh"
        fake_gh.write_text(
            """#!/usr/bin/env python3
import json, sys
endpoint = sys.argv[-1]
if endpoint.endswith("/pulls/3"):
    print(json.dumps({
        "merged_at": "2026-09-21T00:00:00Z",
        "head": {"sha": "__SHA__", "ref": "feature/pr-evidence"},
        "base": {"ref": "main"},
    }))
    raise SystemExit(0)
print("unexpected gh api request", file=sys.stderr)
raise SystemExit(1)
""".replace("__SHA__", pr_evidence_sha),
            encoding="utf-8",
        )
        fake_gh.chmod(0o755)
        cleanup_env = dict(__import__("os").environ)
        cleanup_env["PATH"] = str(fake_bin) + __import__("os").pathsep + cleanup_env["PATH"]

        cleanup_manifest = repo / "cleanup.yaml"
        target_sha = git(repo, "rev-parse", "origin/main")

        stale_manifest = repo / "stale-cleanup.yaml"
        stale_manifest.write_text(yaml.safe_dump({
            "version": 1,
            "cleanup_id": "stale-test",
            "baseline_main_sha": "0" * 40,
            "authorization": {"type": "explicit_user_request", "approved_by": "test-maintainer", "approved_at": "2026-09-21", "scope": "exact_manifest_only", "one_time": True},
            "branches": [{"branch": "feature/merged", "expected_sha": merged_sha, "merged_pr": 1}],
        }, sort_keys=False), encoding="utf-8")
        stale = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin", "--apply-cleanup", str(stale_manifest)],
            cwd=repo, text=True, capture_output=True, check=False,
        )
        assert stale.returncode != 0 and "baseline is stale" in stale.stdout
        assert remote_exists(repo, "feature/merged"), "stale main baseline must block the whole batch"

        absent_manifest = repo / "absent-cleanup.yaml"
        absent_manifest.write_text(yaml.safe_dump({
            "version": 1,
            "cleanup_id": "absent-test",
            "baseline_main_sha": target_sha,
            "authorization": {"type": "explicit_user_request", "approved_by": "test-maintainer", "approved_at": "2026-09-21", "scope": "exact_manifest_only", "one_time": True},
            "branches": [
                {"branch": "feature/merged", "expected_sha": merged_sha, "merged_pr": 1},
                {"branch": "feature/already-missing", "expected_sha": "1" * 40, "merged_pr": 2},
            ],
        }, sort_keys=False), encoding="utf-8")
        absent = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin", "--apply-cleanup", str(absent_manifest)],
            cwd=repo, text=True, capture_output=True, check=False,
        )
        assert absent.returncode != 0 and "consumed, replayed, or partially applied" in absent.stdout
        assert remote_exists(repo, "feature/merged"), "an absent manifest row must block all deletions"

        partial_manifest = repo / "partial-cleanup.yaml"
        partial_manifest.write_text(yaml.safe_dump({
            "version": 1,
            "cleanup_id": "partial-test",
            "baseline_main_sha": target_sha,
            "authorization": {"type": "explicit_user_request", "approved_by": "test-maintainer", "approved_at": "2026-09-21", "scope": "exact_manifest_only", "one_time": True},
            "branches": [
                {"branch": "feature/partial-one", "expected_sha": partial_one_sha, "merged_pr": 4},
                {"branch": "feature/partial-two", "expected_sha": partial_two_sha, "merged_pr": 5},
            ],
        }, sort_keys=False), encoding="utf-8")
        failing_git = fake_bin / "git"
        real_git = shutil.which("git")
        assert real_git, "git executable must be available for failure-injection test"
        failing_git.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = push ]; then\n"
            "  for arg in \"$@\"; do\n"
            "    if [ \"$arg\" = feature/partial-two ]; then echo 'simulated remote failure' >&2; exit 1; fi\n"
            "  done\n"
            "fi\n"
            f"exec {real_git!r} \"$@\"\n",
            encoding="utf-8",
        )
        failing_git.chmod(0o755)
        partial_env = dict(cleanup_env)
        partial_env["PATH"] = str(fake_bin) + __import__("os").pathsep + partial_env["PATH"]
        partial = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin", "--apply-cleanup", str(partial_manifest)],
            cwd=repo, text=True, capture_output=True, env=partial_env,
            check=False,
        )
        assert partial.returncode != 0 and "branches deleted before failure: ['feature/partial-one']" in partial.stdout
        assert not remote_exists(repo, "feature/partial-one")
        assert remote_exists(repo, "feature/partial-two"), "deletion failure must stop before later branches"
        partial_replay = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin", "--apply-cleanup", str(partial_manifest)],
            cwd=repo, text=True, capture_output=True,
            check=False,
        )
        assert partial_replay.returncode != 0 and "consumed, replayed, or partially applied" in partial_replay.stdout
        assert remote_exists(repo, "feature/partial-two"), "partial manifests must not resume on replay"

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
                {"branch": "feature/pr-evidence", "expected_sha": pr_evidence_sha, "merged_pr": 3},
            ],
        }, sort_keys=False), encoding="utf-8")
        cleanup = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin",
             "--apply-cleanup", str(cleanup_manifest), "--github-repository", "owner/repo"],
            cwd=repo, text=True, capture_output=True, env=cleanup_env,
            check=False,
        )
        assert cleanup.returncode == 0, cleanup.stdout + cleanup.stderr
        cleanup_doc = yaml.safe_load(cleanup.stdout)
        assert cleanup_doc["summary"]["deleted"] == 3
        by_branch = {row["branch"]: row for row in cleanup_doc["results"]}
        assert by_branch["feature/pr-evidence"]["integration_proof"] == "GITHUB_MERGED_PR_EXACT_HEAD"
        assert cleanup_doc["authority"]["authorization_scope"] == "exact_manifest_only"
        assert not remote_exists(repo, "feature/merged")
        assert not remote_exists(repo, "feature/squashed")
        assert not remote_exists(repo, "feature/pr-evidence")
        assert remote_exists(repo, "feature/pending")
        assert remote_exists(repo, "feature/retrieval-embedding-trial")

        replay = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(config), "--target", "main", "--remote", "origin",
             "--apply-cleanup", str(cleanup_manifest), "--github-repository", "owner/repo"],
            cwd=repo, text=True, capture_output=True, env=cleanup_env,
            check=False,
        )
        assert replay.returncode != 0 and "consumed, replayed, or partially applied" in replay.stdout

    print("branch hygiene lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
