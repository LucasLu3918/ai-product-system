#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

import yaml

from aips_identity import (
    config_home,
    legacy_path_id,
    project_root,
    repository_identity,
    workspace_snapshot,
)

SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)(password|token|secret|api[_-]?key)\s*[:=]\s*\S+"),
]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _migrate_legacy_run(root: Path, run_id: str, canonical: Path) -> None:
    legacy = config_home() / "projects" / legacy_path_id(root) / "runs" / run_id
    if canonical.exists() or not legacy.exists() or legacy.resolve() == canonical.resolve():
        return
    canonical.parent.mkdir(parents=True, exist_ok=True)
    os.replace(legacy, canonical)
    for parent in (legacy.parent, legacy.parent.parent):
        try:
            parent.rmdir()
        except OSError:
            break


def run_store(root: Path, run_id: str) -> tuple[Path, str]:
    if (root / ".ai").is_dir():
        return root / ".ai" / "runs" / run_id, "ATTACHED"
    ident = repository_identity(root)
    canonical = config_home() / "projects" / ident["workspace_id"] / "runs" / run_id
    _migrate_legacy_run(root, run_id, canonical)
    return canonical, "EPHEMERAL"


def load_yaml(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or ({} if default is None else default)


def atomic_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def safe_text(value: str) -> str:
    value = value[:500]
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value


def update_workspace_state(root: Path, checkpoint: Path, doc: dict) -> None:
    state_path = root / ".ai" / "STATE.yaml"
    if not state_path.exists():
        return
    state = load_yaml(state_path, {})
    workspace = doc.get("workspace") or {}
    state["workflow"] = {
        "run_id": doc["run_id"],
        "protocol": doc.get("protocol"),
        "current_step": doc.get("current_step"),
        "status": doc.get("status"),
        "completed_steps": doc.get("completed_steps") or [],
        "waiting_for": doc.get("waiting_for") or [],
        "resume_from": doc.get("resume_from"),
        "checkpoint": str(checkpoint.relative_to(root)),
        "project_revision": workspace.get("revision"),
        "repository_id": workspace.get("repository_id"),
        "workspace_id": workspace.get("workspace_id"),
        "workspace_fingerprint": workspace.get("fingerprint"),
        "dirty_fingerprint": workspace.get("dirty_fingerprint"),
    }
    state["last_checkpoint"] = {"run_id": doc["run_id"], "updated_at": doc.get("updated_at")}
    atomic_yaml(state_path, state)


def checkpoint(args) -> dict:
    root = project_root(Path(args.project))
    store, mode = run_store(root, args.run_id)
    path = store / "CHECKPOINT.yaml"
    old = load_yaml(path, {})
    completed = list(dict.fromkeys((old.get("completed_steps") or []) + (args.completed_step or [])))
    snap = workspace_snapshot(root)
    workspace = {
        "root": str(root),
        "mode": mode,
        "repository_id": snap.get("repository_id"),
        "workspace_id": snap.get("workspace_id"),
        "revision": snap.get("revision"),
        "branch": snap.get("branch"),
        "dirty_fingerprint": snap.get("dirty_fingerprint"),
        "fingerprint": snap.get("fingerprint"),
        "clean": snap.get("clean"),
    }
    doc = {
        "version": 2,
        "run_id": args.run_id,
        "protocol": args.protocol or old.get("protocol"),
        "status": args.status,
        "current_step": args.step,
        "completed_steps": completed,
        "waiting_for": args.waiting_for or [],
        "resume_from": args.resume_from or args.step,
        "evidence": [safe_text(x) for x in (args.evidence or [])],
        # Legacy compatibility for existing consumers.
        "project": {"root": str(root), "mode": mode, "revision": snap.get("revision")},
        "workspace": workspace,
        "updated_at": now(),
    }
    atomic_yaml(path, doc)
    update_workspace_state(root, path, doc)
    return {
        "checkpoint": str(path),
        "mode": mode,
        "status": doc["status"],
        "revision": workspace["revision"],
        "repository_id": workspace["repository_id"],
        "workspace_id": workspace["workspace_id"],
        "workspace_fingerprint": workspace["fingerprint"],
        "clean": workspace["clean"],
    }


def append_event(args) -> dict:
    root = project_root(Path(args.project))
    store, mode = run_store(root, args.run_id)
    path = store / "EVENTS.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    seq = 1
    if path.exists():
        seq = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()) + 1
    event = {
        "sequence": seq,
        "timestamp": now(),
        "event": safe_text(args.event),
        "status": args.status,
        "artifact": safe_text(args.artifact) if args.artifact else None,
        "evidence": [safe_text(x) for x in (args.evidence or [])],
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return {"events": str(path), "mode": mode, "sequence": seq}


def _freshness(doc: dict, current: dict[str, Any]) -> tuple[bool, list[str], bool]:
    stored = doc.get("workspace") or {}
    reasons: list[str] = []
    if stored.get("fingerprint"):
        if current.get("fingerprint") is None:
            return False, ["workspace_fingerprint_unavailable"], False
        if stored.get("workspace_id") != current.get("workspace_id"):
            reasons.append("workspace_identity_changed")
        if stored.get("revision") != current.get("revision"):
            reasons.append("revision_changed")
        if stored.get("branch") != current.get("branch"):
            reasons.append("branch_changed")
        if stored.get("dirty_fingerprint") != current.get("dirty_fingerprint"):
            reasons.append("dirty_state_changed")
        if stored.get("fingerprint") != current.get("fingerprint") and not reasons:
            reasons.append("workspace_fingerprint_changed")
        return not reasons, reasons, False

    # Legacy v1 checkpoint fallback: never call a dirty workspace CURRENT solely because HEAD matches.
    recorded = (doc.get("project") or {}).get("revision")
    if recorded != current.get("revision"):
        reasons.append("revision_changed")
    if current.get("clean") is not True:
        reasons.append("legacy_checkpoint_requires_clean_workspace")
    if current.get("fingerprint") is None:
        reasons.append("workspace_fingerprint_unavailable")
    return not reasons, reasons, True


def resume(args) -> dict:
    root = project_root(Path(args.project))
    store, mode = run_store(root, args.run_id)
    path = store / "CHECKPOINT.yaml"
    if not path.exists():
        raise RuntimeError("checkpoint not found")
    doc = load_yaml(path, {})
    current = workspace_snapshot(root)
    fresh, reasons, legacy = _freshness(doc, current)
    stored_workspace = doc.get("workspace") or {}
    recorded_revision = stored_workspace.get("revision") or (doc.get("project") or {}).get("revision")
    events_path = store / "EVENTS.jsonl"
    count = 0
    last = None
    if events_path.exists():
        lines = [x for x in events_path.read_text(encoding="utf-8").splitlines() if x.strip()]
        count = len(lines)
        if lines:
            last = json.loads(lines[-1])
    return {
        "status": "CURRENT" if fresh else "STALE",
        "mode": mode,
        "run_id": args.run_id,
        "resume_from": doc.get("resume_from") or doc.get("current_step"),
        "checkpoint": str(path),
        "repository_id": current.get("repository_id"),
        "workspace_id": current.get("workspace_id"),
        "recorded_revision": recorded_revision,
        "current_revision": current.get("revision"),
        "recorded_workspace_fingerprint": stored_workspace.get("fingerprint"),
        "current_workspace_fingerprint": current.get("fingerprint"),
        "requires_freshness_check": not fresh,
        "freshness_reasons": reasons,
        "legacy_checkpoint": legacy,
        "event_count": count,
        "last_event": last,
    }


def output(data: dict, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())


def main() -> int:
    p = argparse.ArgumentParser(description="AIPS durable run state helper")
    sub = p.add_subparsers(dest="command", required=True)
    cp = sub.add_parser("checkpoint")
    cp.add_argument("--project", default=os.getcwd()); cp.add_argument("--run-id", required=True)
    cp.add_argument("--protocol"); cp.add_argument("--step", required=True)
    cp.add_argument("--status", choices=["ACTIVE","WAITING","BLOCKED","COMPLETE"], default="ACTIVE")
    cp.add_argument("--completed-step", action="append"); cp.add_argument("--waiting-for", action="append")
    cp.add_argument("--resume-from"); cp.add_argument("--evidence", action="append")
    cp.add_argument("--format", choices=["yaml","json"], default="yaml")
    ev = sub.add_parser("event")
    ev.add_argument("--project", default=os.getcwd()); ev.add_argument("--run-id", required=True)
    ev.add_argument("--event", required=True); ev.add_argument("--status", default="INFO")
    ev.add_argument("--artifact"); ev.add_argument("--evidence", action="append")
    ev.add_argument("--format", choices=["yaml","json"], default="yaml")
    for name in ("resume","status"):
        q = sub.add_parser(name)
        q.add_argument("--project", default=os.getcwd())
        q.add_argument("--run-id", required=True)
        q.add_argument("--format", choices=["yaml","json"], default="yaml")
    a = p.parse_args()
    try:
        data = checkpoint(a) if a.command == "checkpoint" else append_event(a) if a.command == "event" else resume(a)
    except (RuntimeError, OSError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    output(data, a.format)
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
