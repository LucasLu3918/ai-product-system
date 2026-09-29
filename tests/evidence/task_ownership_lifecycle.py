#!/usr/bin/env python3
"""Exercise scheduler-bound owner leases and final diff reconciliation."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.task_ownership import LEASE_FILE, OwnershipError, _covered, project_ownership, run_command


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def repository(root: Path) -> Path:
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "AIPS lifecycle")
    git(root, "config", "user.email", "aips-lifecycle.invalid")
    (root / "README.md").write_text("base\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-qm", "base")
    return root


def graph(path: Path) -> Path:
    payload = {
        "version": 1,
        "plan_id": "ownership-plan",
        "max_parallel": 2,
        "tasks": [
            {"id": "api", "order": 1, "dependencies": [], "change_boundary": ["src"], "write_set": ["src/**"]},
            {"id": "api-child", "order": 2, "dependencies": [], "change_boundary": ["src/api"], "write_set": ["src/api/**"]},
        ],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def args(action: str, *, project: Path, store: Path, graph_path: Path, state: Path, task: str, execution: str, reason: str = "operator recovery", accept_dirty: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        action=action,
        project=str(project),
        run_id=f"run-{task}",
        task_id=task,
        execution_id=execution,
        state=str(state),
        graph=str(graph_path),
        isolation_id=f"iso-{task}",
        runtime="codex",
        lease_seconds=300,
        reason=reason,
        accept_dirty=accept_dirty,
    )


def invoke(command: argparse.Namespace, store: Path, project: Path) -> dict:
    with patch("run_state.run_store", return_value=(store, "EPHEMERAL")), patch(
        "execution_isolation.status_isolation",
        return_value={"status": "ACTIVE", "mode": "worktree", "exists": True, "path": str(project)},
    ):
        return run_command(command)


def main() -> int:
    assert _covered(".hidden", [".hidden"])
    assert not _covered(".hidden", ["hidden"])

    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        repo = repository(temp / "repo")
        store = temp / "run-store"
        state = temp / "scheduler-state.yaml"
        graph_path = graph(temp / "graph.yaml")

        claimed = invoke(args("claim", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-1"), store, repo)
        owner = claimed["ownership"]
        assert owner["status"] == "ACTIVE"
        assert owner["resource_authorization"]["enforcement_capability"] == "ADVISORY"
        assert owner["resource_authorization"]["write_set"] == ["src/**"]
        state_doc = yaml.safe_load(state.read_text(encoding="utf-8"))
        assert state_doc["tasks"]["api"]["status"] == "RUNNING"
        assert state_doc["tasks"]["api"]["isolation_id"] == "iso-api"

        in_scope = args("authorize", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-1")
        in_scope.path, in_scope.operation = "src/api.py", "update"
        decision = invoke(in_scope, store, repo)["ownership"]
        assert decision["decision"] == "ADVISORY_ALLOW"
        assert decision["enforced"] is False
        outside = args("authorize", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-1")
        outside.path, outside.operation = "outside.py", "update"
        assert invoke(outside, store, repo)["ownership"]["decision"] == "DENY"
        wrong_owner = args("authorize", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-other")
        wrong_owner.path, wrong_owner.operation = "src/api.py", "update"
        assert invoke(wrong_owner, store, repo)["ownership"]["decision"] == "DENY"
        wrong_task = args("authorize", project=repo, store=store, graph_path=graph_path, state=state, task="api-child", execution="exec-1")
        wrong_task.path, wrong_task.operation = "src/api.py", "update"
        assert invoke(wrong_task, store, repo)["ownership"]["decision"] == "DENY"

        # A second claim sharing the scheduler state cannot overlap an active boundary.
        try:
            invoke(args("claim", project=repo, store=temp / "other-run", graph_path=graph_path, state=state, task="api-child", execution="exec-2"), temp / "other-run", repo)
            raise AssertionError("overlapping scheduler dispatch must not be claimed")
        except OwnershipError as exc:
            assert "scheduler has not dispatched" in str(exc)

        (repo / "src").mkdir()
        (repo / "src" / "api.py").write_text("value = 1\n", encoding="utf-8")
        view = project_ownership(store / LEASE_FILE, repo)
        assert view["dirty_files"] == ["src/api.py"]
        reconciled = invoke(args("reconcile", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-1"), store, repo)
        assert reconciled["ownership"]["completion_status"] == "COMPLETE"
        assert reconciled["ownership"]["actual_diff"] == ["src/api.py"]
        state_doc = yaml.safe_load(state.read_text(encoding="utf-8"))
        assert state_doc["tasks"]["api"]["status"] == "COMPLETE"

        # A Git rename is reconciled using both paths, without rename folding.

    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        repo = repository(temp / "repo")
        (repo / "src").mkdir()
        (repo / "src" / "old.py").write_text("old = True\n", encoding="utf-8")
        git(repo, "add", "src/old.py")
        git(repo, "commit", "-qm", "add source")
        store = temp / "run-store"
        state = temp / "scheduler-state.yaml"
        graph_path = graph(temp / "graph.yaml")
        invoke(args("claim", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-rename"), store, repo)
        git(repo, "mv", "src/old.py", "src/new.py")
        renamed = invoke(args("reconcile", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-rename"), store, repo)
        assert renamed["ownership"]["actual_diff"] == ["src/new.py", "src/old.py"]

    # Lease expiry over dirty files requires explicit recovery; it never reassigns.
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        repo = repository(temp / "repo")
        store = temp / "run-store"
        state = temp / "scheduler-state.yaml"
        graph_path = graph(temp / "graph.yaml")
        invoke(args("claim", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-old"), store, repo)
        (repo / "src").mkdir()
        (repo / "src" / "dirty.py").write_text("uncommitted = True\n", encoding="utf-8")
        lease_path = store / "TASK_OWNERSHIP.yaml"
        lease = yaml.safe_load(lease_path.read_text(encoding="utf-8"))
        lease["expires_at"] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        lease_path.write_text(yaml.safe_dump(lease, sort_keys=False), encoding="utf-8")
        try:
            invoke(args("heartbeat", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-old"), store, repo)
            raise AssertionError("expired dirty lease must not heartbeat")
        except OwnershipError as exc:
            assert "requires explicit recovery" in str(exc)
        stale = yaml.safe_load(lease_path.read_text(encoding="utf-8"))
        assert stale["status"] == "STALE"
        assert stale["recovery_status"] == "RECOVERY_REQUIRED"
        try:
            invoke(args("claim", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-new"), store, repo)
            raise AssertionError("stale task must not be automatically reassigned")
        except OwnershipError as exc:
            assert "scheduler has not dispatched" in str(exc)
        wrong_isolation = args("recover", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-new", accept_dirty=True)
        wrong_isolation.isolation_id = "different-active-worktree"
        try:
            invoke(wrong_isolation, store, repo)
            raise AssertionError("recovery must remain bound to the original isolation")
        except OwnershipError as exc:
            assert "original AIPS-managed worktree isolation" in str(exc)
        with patch("scripts.task_ownership._atomic_yaml", side_effect=OSError("simulated lease write interruption")):
            try:
                invoke(args("recover", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-new", accept_dirty=True), store, repo)
                raise AssertionError("simulated lease write failure should be surfaced")
            except OSError as exc:
                assert "simulated lease write interruption" in str(exc)
        state_doc = yaml.safe_load(state.read_text(encoding="utf-8"))
        assert state_doc["tasks"]["api"]["execution_id"] == "exec-new"
        recovered = invoke(args("recover", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-new", accept_dirty=True), store, repo)
        assert recovered["ownership"]["status"] == "ACTIVE"
        assert recovered["ownership"]["recovery_status"] == "RECOVERY_IN_PROGRESS"
        done = invoke(args("reconcile", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-new"), store, repo)
        assert done["ownership"]["completion_status"] == "COMPLETE"

    # Two simultaneous claims serialize through one scheduler-state lock.
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        repo = repository(temp / "repo")
        state = temp / "scheduler-state.yaml"
        graph_path = graph(temp / "graph.yaml")
        stores = temp / "stores"
        stores.mkdir()

        def simultaneous(task: str) -> str:
            command = args("claim", project=repo, store=stores / task, graph_path=graph_path, state=state, task=task, execution=f"exec-{task}")
            try:
                with patch("run_state.run_store", return_value=(stores / task, "EPHEMERAL")), patch(
                    "execution_isolation.status_isolation",
                    return_value={"status": "ACTIVE", "mode": "worktree", "exists": True, "path": str(repo)},
                ):
                    run_command(command)
                return "CLAIMED"
            except OwnershipError:
                return "DEFERRED"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(simultaneous, ["api", "api-child"]))
        assert sorted(results) == ["CLAIMED", "DEFERRED"], results
        state_doc = yaml.safe_load(state.read_text(encoding="utf-8"))
        assert sum(value["status"] == "RUNNING" for value in state_doc["tasks"].values()) == 1

    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        repo = repository(temp / "repo")
        store = temp / "run-store"
        state = temp / "scheduler-state.yaml"
        graph_path = graph(temp / "graph.yaml")
        invoke(args("claim", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-1"), store, repo)
        (repo / "outside.txt").write_text("outside declared write set\n", encoding="utf-8")
        try:
            invoke(args("reconcile", project=repo, store=store, graph_path=graph_path, state=state, task="api", execution="exec-1"), store, repo)
            raise AssertionError("out-of-scope changes must block completion")
        except OwnershipError as exc:
            assert "exceeds write_set" in str(exc)
        state_doc = yaml.safe_load(state.read_text(encoding="utf-8"))
        assert state_doc["tasks"]["api"]["status"] == "BLOCKED"

    print("task ownership lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
