#!/usr/bin/env python3
"""Durable, fail-closed task ownership leases for AIPS run state."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from deterministic_scheduler import normalize_boundaries, write_set_within_boundary

LEASE_FILE = "TASK_OWNERSHIP.yaml"
LEASE_LOCK = "TASK_OWNERSHIP.yaml.lock"


class OwnershipError(ValueError):
    pass


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def timestamp(value: dt.datetime | None = None) -> str:
    value = value or now()
    return value.isoformat().replace("+00:00", "Z")


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False, timeout=15
    )
    if proc.returncode:
        raise OwnershipError(proc.stderr.strip() or "git inspection failed")
    return proc.stdout.strip()


def current_changes(root: Path, base_revision: str) -> list[str]:
    tracked = subprocess.run(
        ["git", "-C", str(root), "diff", "--no-renames", "--name-only", "-z", base_revision, "--"],
        capture_output=True,
        check=False,
        timeout=15,
    )
    untracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "-z"],
        capture_output=True,
        check=False,
        timeout=15,
    )
    if tracked.returncode or untracked.returncode:
        raise OwnershipError("unable to inspect the actual worktree diff")
    names = set()
    for blob in (tracked.stdout, untracked.stdout):
        names.update(item.decode("utf-8", errors="surrogateescape") for item in blob.split(b"\0") if item)
    return sorted(names)


def _covered(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatchcase(normalized, pattern) for pattern in patterns)


def _boundary_covers(path: str, boundaries: list[str]) -> bool:
    for boundary in boundaries:
        if any(char in boundary for char in "*?["):
            if fnmatch.fnmatchcase(path, boundary):
                return True
        elif path == boundary or path.startswith(boundary.rstrip("/") + "/"):
            return True
    return False


def _atomic_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            yaml.safe_dump(data, output, sort_keys=False, allow_unicode=True)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _locked(path: Path):
    if path.exists() and path.is_dir():
        path.mkdir(parents=True, exist_ok=True)
        lock_path = path / LEASE_LOCK
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = path.with_suffix(path.suffix + ".lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    return os.fdopen(fd, "r+b")


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise OwnershipError("task ownership state must be a mapping")
    return data


def _expire(doc: dict[str, Any], root: Path) -> bool:
    if doc.get("status") != "ACTIVE":
        return False
    try:
        expires = dt.datetime.fromisoformat(str(doc["expires_at"]).replace("Z", "+00:00"))
    except (KeyError, ValueError, TypeError):
        doc["status"] = "ORPHANED"
        doc["recovery_status"] = "RECOVERY_REQUIRED"
        doc["recovery_reason"] = "lease_expiry_unverifiable"
        return True
    if expires > now():
        return False
    if not root.is_dir():
        dirty = list(doc.get("observed_dirty_files") or [])
        doc["status"] = "ORPHANED"
    else:
        dirty = current_changes(root, str(doc.get("base_revision") or "HEAD"))
        doc["status"] = "STALE"
    doc["observed_dirty_files"] = dirty
    doc["recovery_status"] = "RECOVERY_REQUIRED" if dirty else "RELEASE_REQUIRED"
    doc["recovery_reason"] = "lease_expired"
    doc["updated_at"] = timestamp()
    return True


def _event(store: Path, name: str, status: str, task_id: str, execution_id: str, evidence: list[str] | None = None) -> None:
    from run_event_stream import append_event
    from run_state import safe_text

    safe_names = [safe_text(value) for value in (evidence or [])]
    append_event(
        store / "EVENTS.jsonl",
        {
            "timestamp": timestamp(),
            "event": name,
            "status": status,
            "artifact": None,
            "evidence": [f"task={task_id}", f"execution={execution_id}", *safe_names],
        },
    )


def claim(
    root: Path,
    store: Path,
    *,
    task_id: str,
    execution_id: str,
    boundary: list[str],
    write_set: list[str],
    dependencies: list[str],
    read_set: list[str],
    lease_seconds: int,
    runtime: str,
    isolation_id: str,
) -> dict[str, Any]:
    if not task_id.strip() or not execution_id.strip() or not isolation_id.strip():
        raise OwnershipError("task_id, execution_id and isolation_id are required")
    if lease_seconds < 30 or lease_seconds > 86400:
        raise OwnershipError("lease_seconds must be between 30 and 86400")
    boundaries = normalize_boundaries(boundary)
    if not boundaries:
        if write_set:
            raise OwnershipError("a writable task requires a non-empty Change Boundary")
    elif write_set and not write_set_within_boundary(write_set, boundaries):
        raise OwnershipError("write_set must be contained in Change Boundary")
    path = store / LEASE_FILE
    with _locked(store) as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            old = _read(path)
            if old:
                _expire(old, root)
                if old.get("status") == "ACTIVE":
                    if old.get("execution_id") == execution_id and old.get("task_id") == task_id:
                        return old
                    _atomic_yaml(path, old)
                    raise OwnershipError("task already has an active execution owner")
                if old.get("status") in {"STALE", "ORPHANED", "BLOCKED", "RECOVERY_REQUIRED"}:
                    _atomic_yaml(path, old)
                    raise OwnershipError("stale or orphaned ownership requires explicit recovery before reassignment")
            if _git(root, "status", "--porcelain"):
                raise OwnershipError("task ownership claim requires a clean worktree")
            base = _git(root, "rev-parse", "HEAD")
            ident = root.name
            try:
                from aips_identity import workspace_snapshot

                snapshot = workspace_snapshot(root)
                ident = snapshot.get("workspace_id") or ident
                branch = snapshot.get("branch") or "UNKNOWN"
            except (OSError, ValueError, RuntimeError):
                branch = "UNKNOWN"
            issued = now()
            doc = {
                "version": 1,
                "task_id": task_id,
                "execution_id": execution_id,
                "runtime": runtime,
                "isolation_id": isolation_id,
                "isolation_mode": "worktree",
                "status": "ACTIVE",
                "change_boundary": list(boundaries),
                "write_set": sorted(set(write_set)),
                "read_set": sorted(set(read_set)),
                "dependencies": sorted(set(dependencies)),
                "workspace_id": ident,
                "branch": branch,
                "base_revision": base,
                "claimed_at": timestamp(issued),
                "heartbeat_at": timestamp(issued),
                "expires_at": timestamp(issued + dt.timedelta(seconds=lease_seconds)),
                "lease_seconds": lease_seconds,
                "observed_dirty_files": [],
                "recovery_status": "NONE",
                "resource_authorization": {
                    "source": "task_write_set",
                    "effect": "DENY_OUTSIDE_WRITE_SET",
                    "change_boundary": list(boundaries),
                    "write_set": sorted(set(write_set)),
                    "enforcement_capability": "ADVISORY",
                    "capability_verified": False,
                    "reason": "no verified runtime write guard is connected",
                },
            }
            _atomic_yaml(path, doc)
            _event(store, "task.claimed", "INFO", task_id, execution_id)
            return doc
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def transition(root: Path, store: Path, action: str, task_id: str, execution_id: str, *, lease_seconds: int = 300) -> dict[str, Any]:
    path = store / LEASE_FILE
    with _locked(store) as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            doc = _read(path)
            if not doc:
                raise OwnershipError("task has no ownership lease")
            if doc.get("task_id") != task_id:
                raise OwnershipError("run lease belongs to a different task")
            if doc.get("execution_id") != execution_id:
                raise OwnershipError("execution does not own this task lease")
            # A process may stop after the lease is persisted but before the
            # shared scheduler state is updated. Allow that same command to
            # finish its second write safely.
            if action == "reconcile" and doc.get("status") == "RECONCILED":
                return doc
            if action == "release" and doc.get("status") == "RELEASED":
                return doc
            changed = _expire(doc, root)
            if changed:
                _atomic_yaml(path, doc)
                _event(store, "task.orphaned" if doc["status"] == "ORPHANED" else "task.stale", "BLOCKED", str(doc.get("task_id")), execution_id, doc.get("observed_dirty_files", []))
                raise OwnershipError("lease expired; task requires explicit recovery")
            if doc.get("status") != "ACTIVE":
                raise OwnershipError("task lease is not active; explicit recovery is required")
            if action == "heartbeat":
                if doc.get("status") != "ACTIVE":
                    raise OwnershipError("only an active lease can heartbeat")
                if lease_seconds < 30 or lease_seconds > 86400:
                    raise OwnershipError("lease_seconds must be between 30 and 86400")
                stamp = now()
                doc["heartbeat_at"] = timestamp(stamp)
                doc["expires_at"] = timestamp(stamp + dt.timedelta(seconds=lease_seconds))
                doc["updated_at"] = timestamp(stamp)
                _atomic_yaml(path, doc)
                _event(store, "task.heartbeat", "INFO", str(doc["task_id"]), execution_id)
                return doc
            if action == "release":
                dirty = current_changes(root, str(doc["base_revision"]))
                if dirty:
                    doc["status"] = "RECOVERY_REQUIRED"
                    doc["observed_dirty_files"] = dirty
                    doc["recovery_status"] = "RECOVERY_REQUIRED"
                    doc["updated_at"] = timestamp()
                    _atomic_yaml(path, doc)
                    _event(store, "task.orphaned", "BLOCKED", str(doc["task_id"]), execution_id, dirty)
                    raise OwnershipError("dirty work cannot release ownership; reconcile it or recover explicitly")
                doc["status"] = "RELEASED"
                doc["released_at"] = timestamp()
                doc["recovery_status"] = "NONE"
                _atomic_yaml(path, doc)
                _event(store, "task.released", "INFO", str(doc["task_id"]), execution_id)
                return doc
            if action == "reconcile":
                actual = current_changes(root, str(doc["base_revision"]))
                allowed = list(doc.get("write_set") or [])
                out_of_scope = [item for item in actual if not _covered(item, allowed)]
                doc["actual_diff"] = actual
                doc["out_of_scope_files"] = out_of_scope
                doc["reconciled_at"] = timestamp()
                if out_of_scope:
                    doc["status"] = "BLOCKED"
                    doc["recovery_status"] = "RECOVERY_REQUIRED"
                    doc["recovery_reason"] = "actual_diff_exceeds_write_set"
                    _atomic_yaml(path, doc)
                    _event(store, "task.reconciled", "BLOCKED", str(doc["task_id"]), execution_id, out_of_scope)
                    raise OwnershipError("actual Git diff exceeds write_set; task completion is blocked")
                doc["status"] = "RECONCILED"
                doc["completion_status"] = "COMPLETE"
                doc["recovery_status"] = "NONE"
                _atomic_yaml(path, doc)
                _event(store, "task.reconciled", "PASS", str(doc["task_id"]), execution_id, actual)
                return doc
            raise OwnershipError(f"unsupported ownership action: {action}")
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def recover(
    root: Path,
    store: Path,
    state_path: Path,
    *,
    task_id: str,
    execution_id: str,
    isolation_id: str,
    reason: str,
    accept_dirty: bool,
    lease_seconds: int,
) -> dict[str, Any]:
    from run_state import atomic_yaml, load_yaml, safe_text

    path = store / LEASE_FILE
    with _locked(store) as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            doc = _read(path)
            if doc.get("status") == "ACTIVE" and _expire(doc, root):
                _atomic_yaml(path, doc)
            if doc.get("task_id") != task_id or doc.get("status") not in {"STALE", "ORPHANED", "RECOVERY_REQUIRED", "BLOCKED"}:
                raise OwnershipError("only a stale, orphaned or blocked task can be explicitly recovered")
            if doc.get("isolation_id") != isolation_id or doc.get("isolation_mode") != "worktree":
                raise OwnershipError("recovery must use the task's original AIPS-managed worktree isolation")
            if not reason.strip():
                raise OwnershipError("recovery requires an explicit reason")
            if lease_seconds < 30 or lease_seconds > 86400:
                raise OwnershipError("lease_seconds must be between 30 and 86400")
            if not root.is_dir():
                raise OwnershipError("orphaned worktree is missing; recovery must occur after isolation is restored")
            actual = current_changes(root, str(doc.get("base_revision") or "HEAD"))
            if actual and not accept_dirty:
                raise OwnershipError("dirty recovery requires explicit --accept-dirty acknowledgement")
            state = load_yaml(state_path, {"tasks": {}})
            task_state = (state.get("tasks") or {}).get(task_id, {})
            task_state = task_state if isinstance(task_state, dict) else {"status": task_state}
            if task_state.get("status") not in {"RUNNING", "BLOCKED"}:
                raise OwnershipError("scheduler state does not allow recovery of this task")
            if task_state.get("execution_id") not in (None, doc.get("execution_id"), execution_id):
                raise OwnershipError("scheduler state names a different execution owner")
            stamp = now()
            doc["previous_execution_id"] = doc.get("execution_id")
            doc["execution_id"] = execution_id
            doc["status"] = "ACTIVE"
            doc["recovery_status"] = "RECOVERY_IN_PROGRESS" if actual else "NONE"
            doc["recovery_reason"] = safe_text(reason)
            doc["recovery_accepted_dirty"] = bool(actual and accept_dirty)
            doc["observed_dirty_files"] = actual
            doc["heartbeat_at"] = timestamp(stamp)
            doc["expires_at"] = timestamp(stamp + dt.timedelta(seconds=lease_seconds))
            doc["updated_at"] = timestamp(stamp)
            tasks = state.setdefault("tasks", {})
            tasks[task_id] = {
                **task_state,
                "status": "RUNNING",
                "execution_id": execution_id,
                "recovered_from": doc["previous_execution_id"],
            }
            # Persist the shared scheduler owner first. If the lease write
            # fails, retrying this exact recovery remains idempotent because
            # the requested execution is now an accepted recovery owner.
            atomic_yaml(state_path, state)
            _atomic_yaml(path, doc)
            _event(store, "task.recovered", "WARN", task_id, execution_id, actual)
            return doc
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def project_ownership(path: Path | None, worktree_root: Path | None = None) -> dict[str, Any]:
    if not path or not path.is_file():
        return {
            "task_id": "UNASSIGNED",
            "owner_execution_id": "UNKNOWN",
            "lease_status": "UNASSIGNED",
            "change_boundary": [],
            "write_set": [],
            "dependencies": [],
            "worktree": "UNKNOWN",
            "dirty_files": [],
            "heartbeat_at": None,
            "enforcement_capability": "UNKNOWN",
            "recovery_status": "NONE",
        }
    doc = _read(path)
    status = str(doc.get("status") or "UNKNOWN").upper()
    try:
        expires = dt.datetime.fromisoformat(str(doc.get("expires_at") or "").replace("Z", "+00:00"))
        if status == "ACTIVE" and expires <= now():
            status = "STALE"
    except ValueError:
        pass
    dirty = list(doc.get("observed_dirty_files") or doc.get("actual_diff") or [])
    if worktree_root is not None and worktree_root.is_dir() and doc.get("base_revision"):
        try:
            dirty = current_changes(worktree_root, str(doc["base_revision"]))
        except (OSError, OwnershipError, subprocess.SubprocessError):
            pass
    recovery = doc.get("recovery_status") or "NONE"
    if status in {"STALE", "ORPHANED", "BLOCKED"}:
        recovery = "RECOVERY_REQUIRED" if dirty else "RELEASE_REQUIRED"
    auth = doc.get("resource_authorization") or {}
    return {
        "task_id": doc.get("task_id") or "UNKNOWN",
        "owner_execution_id": doc.get("execution_id") or "UNKNOWN",
        "lease_status": status,
        "change_boundary": list(doc.get("change_boundary") or []),
        "write_set": list(doc.get("write_set") or []),
        "dependencies": list(doc.get("dependencies") or []),
        "worktree": doc.get("workspace_id") or "UNKNOWN",
        "branch": doc.get("branch") or "UNKNOWN",
        "dirty_files": dirty,
        "heartbeat_at": doc.get("heartbeat_at"),
        "expires_at": doc.get("expires_at"),
        "enforcement_capability": auth.get("enforcement_capability", "UNKNOWN"),
        "recovery_status": recovery,
        "completion_status": doc.get("completion_status"),
    }


def authorize(path: Path, *, task_id: str, operation: str, execution_id: str, record_path: Path) -> dict[str, Any]:
    doc = _read(record_path)
    current = project_ownership(record_path)
    relative = path.as_posix()
    normalized = relative
    valid = bool(normalized) and not path.is_absolute() and "\\" not in relative and all(
        part not in {"", ".", ".."} for part in relative.split("/")
    )
    if not valid:
        decision, reason = "DENY", "resource_path_must_be_normalized_and_repository_relative"
    elif doc.get("task_id") != task_id:
        decision, reason = "DENY", "run_lease_belongs_to_another_task"
    elif doc.get("status") != "ACTIVE" or current.get("lease_status") != "ACTIVE":
        decision, reason = "DENY", "task_lease_is_not_active"
    elif doc.get("execution_id") != execution_id:
        decision, reason = "DENY", "execution_does_not_own_task_lease"
    else:
        write_operation = operation in {"create", "update", "delete"}
        patterns = list(doc.get("write_set") or []) if write_operation else [
            *list(doc.get("read_set") or []), *list(doc.get("write_set") or [])
        ]
        if _covered(normalized, patterns) and _boundary_covers(normalized, list(doc.get("change_boundary") or [])):
            decision, reason = "ADVISORY_ALLOW", "within_task_write_set_and_change_boundary"
        else:
            decision, reason = "DENY", "outside_task_write_set_or_change_boundary"
    auth = doc.get("resource_authorization") or {}
    return {
        "decision": decision,
        "reason": reason,
        "task_id": doc.get("task_id", "UNKNOWN"),
        "execution_id": execution_id,
        "resource": normalized if valid else "INVALID_PATH",
        "operation": operation,
        "enforcement_capability": auth.get("enforcement_capability", "UNKNOWN"),
        "enforced": False,
        "authority": "advisory_only",
    }


def run_command(args: argparse.Namespace) -> dict[str, Any]:
    from run_state import atomic_yaml, load_yaml, project_root, run_store
    from deterministic_scheduler import schedule, validate_graph

    root = project_root(Path(args.project))
    store, mode = run_store(root, args.run_id)
    store.mkdir(parents=True, exist_ok=True)
    if args.action == "claim":
        state_path = Path(args.state).expanduser().resolve()
        graph = yaml.safe_load(Path(args.graph).expanduser().read_text(encoding="utf-8")) or {}
        by_id = validate_graph(graph)
        task = by_id.get(args.task_id)
        if task is None:
            raise OwnershipError("task_id is not present in the Task Graph")
        with _locked(state_path) as state_lock:
            fcntl.flock(state_lock.fileno(), fcntl.LOCK_EX)
            try:
                current_state = load_yaml(state_path, {"plan_id": graph.get("plan_id"), "tasks": {}})
                current_task = (current_state.get("tasks") or {}).get(args.task_id, {})
                current_task = current_task if isinstance(current_task, dict) else {"status": current_task}
                decision = schedule(graph, current_state)
                same_owner = current_task.get("status") == "RUNNING" and current_task.get("execution_id") == args.execution_id
                if args.task_id not in decision["dispatch"] and not same_owner:
                    raise OwnershipError("scheduler has not dispatched this task")
                if current_task.get("status") == "RUNNING" and current_task.get("execution_id") not in (None, args.execution_id):
                    raise OwnershipError("task is already assigned to another execution")
                from execution_isolation import status_isolation

                isolation = status_isolation(SimpleNamespace(project=str(root), id=args.isolation_id))
                if (
                    isolation.get("status") != "ACTIVE"
                    or isolation.get("mode") != "worktree"
                    or isolation.get("exists") is not True
                    or Path(str(isolation.get("path") or "")).resolve() != root.resolve()
                ):
                    raise OwnershipError("isolation_id must identify this active AIPS-managed worktree")
                result = claim(
                    root, store, task_id=args.task_id, execution_id=args.execution_id,
                    boundary=list(task["change_boundary"]), write_set=list(task["write_set"]),
                    dependencies=list(task["dependencies"]), read_set=list(task.get("read_set") or []), lease_seconds=args.lease_seconds,
                    runtime=args.runtime, isolation_id=args.isolation_id,
                )
                tasks = current_state.setdefault("tasks", {})
                tasks[args.task_id] = {**current_task, "status": "RUNNING", "execution_id": args.execution_id, "run_id": args.run_id, "isolation_id": args.isolation_id}
                atomic_yaml(state_path, current_state)
            finally:
                fcntl.flock(state_lock.fileno(), fcntl.LOCK_UN)
    elif args.action == "status":
        result = project_ownership(store / LEASE_FILE)
    elif args.action == "authorize":
        result = authorize(Path(args.path), task_id=args.task_id, operation=args.operation, execution_id=args.execution_id, record_path=store / LEASE_FILE)
    elif args.action == "recover":
        state_path = Path(args.state).expanduser().resolve()
        with _locked(state_path) as state_lock:
            fcntl.flock(state_lock.fileno(), fcntl.LOCK_EX)
            try:
                from execution_isolation import status_isolation

                isolation = status_isolation(SimpleNamespace(project=str(root), id=args.isolation_id))
                if (
                    isolation.get("status") != "ACTIVE"
                    or isolation.get("mode") != "worktree"
                    or isolation.get("exists") is not True
                    or Path(str(isolation.get("path") or "")).resolve() != root.resolve()
                ):
                    raise OwnershipError("recovery requires the task's active AIPS-managed worktree")
                result = recover(
                    root, store, state_path, task_id=args.task_id,
                    execution_id=args.execution_id, isolation_id=args.isolation_id, reason=args.reason,
                    accept_dirty=args.accept_dirty, lease_seconds=args.lease_seconds,
                )
            finally:
                fcntl.flock(state_lock.fileno(), fcntl.LOCK_UN)
    else:
        state_path = Path(args.state).expanduser().resolve()
        with _locked(state_path) as state_lock:
            fcntl.flock(state_lock.fileno(), fcntl.LOCK_EX)
            try:
                state = load_yaml(state_path, {"tasks": {}})
                task_state = (state.get("tasks") or {}).get(args.task_id, {})
                task_state = task_state if isinstance(task_state, dict) else {"status": task_state}
                if task_state.get("status") != "RUNNING" or task_state.get("execution_id") != args.execution_id:
                    raise OwnershipError("scheduler state does not assign this task to the execution")
                result = transition(root, store, args.action, args.task_id, args.execution_id, lease_seconds=args.lease_seconds)
                new_status = "COMPLETE" if args.action == "reconcile" else "PENDING"
                state.setdefault("tasks", {})[args.task_id] = {**task_state, "status": new_status}
                atomic_yaml(state_path, state)
            except OwnershipError:
                state = load_yaml(state_path, {"tasks": {}})
                lease = _read(store / LEASE_FILE)
                if lease.get("status") == "BLOCKED":
                    task_state = state.setdefault("tasks", {}).get(args.task_id, {})
                    task_state = task_state if isinstance(task_state, dict) else {"status": task_state}
                    state.setdefault("tasks", {})[args.task_id] = {**task_state, "status": "BLOCKED"}
                    atomic_yaml(state_path, state)
                raise
            finally:
                fcntl.flock(state_lock.fileno(), fcntl.LOCK_UN)
    return {"mode": mode, "ownership": result}


def add_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("owner", help="claim and inspect deterministic task ownership leases")
    actions = parser.add_subparsers(dest="action", required=True)
    for name in ("claim", "heartbeat", "status", "release", "reconcile", "recover", "authorize"):
        item = actions.add_parser(name)
        item.add_argument("--project", default=os.getcwd())
        item.add_argument("--run-id", required=True)
        if name not in {"status"}:
            item.add_argument("--execution-id", required=name != "claim")
        if name in {"claim", "heartbeat", "release", "reconcile"}:
            item.add_argument("--state", required=True, help="shared scheduler state YAML")
        if name == "claim":
            item.add_argument("--task-id", required=True)
            item.add_argument("--graph", required=True, help="canonical Task Graph YAML")
            item.add_argument("--isolation-id", required=True)
            item.add_argument("--runtime", default="unknown")
        elif name != "status":
            item.add_argument("--task-id", required=True)
        if name == "recover":
            item.add_argument("--isolation-id", required=True)
            item.add_argument("--reason", required=True)
            item.add_argument("--accept-dirty", action="store_true")
        if name == "authorize":
            item.add_argument("--path", required=True)
            item.add_argument("--operation", choices=("read", "search", "create", "update", "delete"), required=True)
        item.add_argument("--lease-seconds", type=int, default=300)
        item.add_argument("--format", choices=("yaml", "json"), default="yaml")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    add_parser(sub)
    args = parser.parse_args()
    try:
        result = run_command(args)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError, yaml.YAMLError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
