#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
IDENTITY = ROOT / "scripts" / "aips_identity.py"
RUN_STATE = ROOT / "scripts" / "run_state.py"
INTELLIGENCE = ROOT / "scripts" / "project_intelligence.py"
ISOLATION = ROOT / "scripts" / "execution_isolation.py"
CLI = ROOT / "bin" / "aips"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(args: list[str], *, env: dict[str, str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, cwd=cwd, capture_output=True, text=True)


def git(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=project, capture_output=True, text=True, check=True)


def json_run(args: list[str], env: dict[str, str]) -> dict:
    result = run(args, env=env)
    require(result.returncode == 0, f"command failed: {args}: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        peer = base / "peer-worktree"
        config = base / "config"
        project.mkdir()
        (project / "README.md").write_text("base\n", encoding="utf-8")
        git(project, "init", "-q")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Test")
        git(project, "remote", "add", "origin", "https://example.invalid/acme/demo.git")
        git(project, "add", "README.md")
        git(project, "commit", "-qm", "initial")

        env = dict(os.environ)
        env["XDG_CONFIG_HOME"] = str(config)

        main_identity = json_run(
            [sys.executable, str(IDENTITY), "show", "--project", str(project), "--format", "json"], env
        )
        cli_identity = json_run(
            ["bash", str(CLI), "identity", "--project", str(project), "--format", "json"], env
        )
        require(
            cli_identity["identity"]["workspace_id"] == main_identity["identity"]["workspace_id"],
            "CLI identity must match canonical identity helper",
        )

        git(project, "worktree", "add", "-q", "-b", "peer", str(peer), "HEAD")
        peer_identity = json_run(
            [sys.executable, str(IDENTITY), "show", "--project", str(peer), "--format", "json"], env
        )
        require(
            main_identity["identity"]["repository_id"] == peer_identity["identity"]["repository_id"],
            "worktrees of one repository must share repository_id",
        )
        require(
            main_identity["identity"]["workspace_id"] != peer_identity["identity"]["workspace_id"],
            "distinct worktrees must have distinct workspace_id",
        )

        boot = json_run(
            [sys.executable, str(INTELLIGENCE), "bootstrap", "--project", str(project), "--format", "json"], env
        )
        workspace_id = main_identity["identity"]["workspace_id"]
        require(workspace_id in boot["store"], "Project Intelligence must use canonical workspace namespace")
        require(not (project / ".ai").exists(), "EPHEMERAL Intelligence must not create .ai")

        cp = json_run(
            [
                sys.executable, str(RUN_STATE), "checkpoint", "--project", str(project),
                "--run-id", "r1", "--step", "implementation", "--format", "json",
            ],
            env,
        )
        require(cp["workspace_id"] == workspace_id, "Run checkpoint must use canonical workspace_id")
        current = json_run(
            [sys.executable, str(RUN_STATE), "resume", "--project", str(project), "--run-id", "r1", "--format", "json"],
            env,
        )
        require(current["status"] == "CURRENT", "unchanged workspace must resume CURRENT")

        (project / "README.md").write_text("dirty\n", encoding="utf-8")
        stale = json_run(
            [sys.executable, str(RUN_STATE), "resume", "--project", str(project), "--run-id", "r1", "--format", "json"],
            env,
        )
        require(stale["status"] == "STALE", "dirty change with same HEAD must stale resume")
        require("dirty_state_changed" in stale["freshness_reasons"], "dirty-state reason missing")
        git(project, "checkout", "--", "README.md")
        current_again = json_run(
            [sys.executable, str(RUN_STATE), "resume", "--project", str(project), "--run-id", "r1", "--format", "json"],
            env,
        )
        require(current_again["status"] == "CURRENT", "restored workspace should match checkpoint fingerprint")

        revision = git(project, "rev-parse", "HEAD").stdout.strip()
        legacy_id = hashlib.sha256(str(project.resolve()).encode()).hexdigest()[:20]
        legacy_run = config / "aips" / "projects" / legacy_id / "runs" / "legacy"
        legacy_run.mkdir(parents=True)
        (legacy_run / "CHECKPOINT.yaml").write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "run_id": "legacy",
                    "status": "ACTIVE",
                    "current_step": "implementation",
                    "resume_from": "implementation",
                    "project": {"root": str(project), "mode": "EPHEMERAL", "revision": revision},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        migrated = json_run(
            [
                sys.executable, str(RUN_STATE), "resume", "--project", str(project),
                "--run-id", "legacy", "--format", "json",
            ],
            env,
        )
        canonical_legacy = config / "aips" / "projects" / workspace_id / "runs" / "legacy" / "CHECKPOINT.yaml"
        require(migrated["legacy_checkpoint"] is True, "legacy checkpoint compatibility flag missing")
        require(migrated["status"] == "CURRENT", "clean matching legacy checkpoint should remain resumable")
        require(canonical_legacy.exists(), "legacy external run was not migrated to canonical namespace")
        require(not (legacy_run / "CHECKPOINT.yaml").exists(), "legacy external run copy should be moved")

        (project / ".ai").mkdir()
        attached_cp = json_run(
            [
                sys.executable, str(RUN_STATE), "checkpoint", "--project", str(project),
                "--run-id", "attached", "--step", "review", "--format", "json",
            ],
            env,
        )
        attached_resume = json_run(
            [
                sys.executable, str(RUN_STATE), "resume", "--project", str(project),
                "--run-id", "attached", "--format", "json",
            ],
            env,
        )
        require(attached_cp["mode"] == "ATTACHED", "attached checkpoint mode missing")
        require(attached_resume["status"] == "CURRENT", "AIPS-owned .ai checkpoint writes must not stale the workspace")
        # Remove local AIPS state so the remaining Git worktree checks see only product state.
        import shutil
        shutil.rmtree(project / ".ai")

        iso1 = json_run(
            [
                sys.executable, str(ISOLATION), "create", "--project", str(project),
                "--mode", "worktree", "--id", "iso1", "--boundary", "orders", "--format", "json",
            ],
            env,
        )
        require(
            iso1["repository_id"] == main_identity["identity"]["repository_id"],
            "Isolation record must use canonical repository_id",
        )
        duplicate = run(
            [
                sys.executable, str(ISOLATION), "create", "--project", str(peer),
                "--mode", "worktree", "--id", "iso2", "--boundary", "orders", "--format", "json",
            ],
            env=env,
        )
        require(duplicate.returncode != 0, "same repository/boundary writer from another worktree must be blocked")

        removed = json_run(
            [
                sys.executable, str(ISOLATION), "remove", "--project", str(peer),
                "--id", "iso1", "--format", "json",
            ],
            env,
        )
        require(removed["status"] == "REMOVED", "cross-worktree isolation cleanup failed")

        git(project, "worktree", "remove", str(peer))

    print("identity_resume_isolation evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
