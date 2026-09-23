#!/usr/bin/env python3
"""Build a deterministic, read-only operational view of AIPS runs."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aips_identity import config_home, project_root, repository_identity, workspace_snapshot
from run_state import _freshness, load_yaml, safe_text

SCHEMA_VERSION = 1
MAX_EVENTS = 20
MAX_RUNS = 200


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git(root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _worktree_roots(root: Path) -> list[Path]:
    roots = {root.resolve()}
    raw = _git(root, "worktree", "list", "--porcelain")
    for line in raw.splitlines():
        if line.startswith("worktree "):
            candidate = Path(line.removeprefix("worktree ")).expanduser()
            if candidate.is_dir():
                roots.add(candidate.resolve())
    return sorted(roots, key=str)


def _workspace_catalog(root: Path) -> dict[str, Path | None]:
    catalog: dict[str, Path | None] = {}
    repo_id = repository_identity(root)["repository_id"]
    for candidate in _worktree_roots(root):
        identity = repository_identity(candidate)
        if identity["repository_id"] == repo_id:
            catalog[identity["workspace_id"]] = candidate

    # EPHEMERAL runs live outside the repository. Only inspect directories that
    # are namespaced by this repository identity; never walk arbitrary config.
    projects = config_home() / "projects"
    if projects.is_dir():
        prefix = repo_id + "-"
        for candidate in projects.iterdir():
            if candidate.is_dir() and candidate.name.startswith(prefix):
                catalog.setdefault(candidate.name, None)
    return catalog


def _run_candidates(root: Path, catalog: dict[str, Path | None]) -> Iterable[tuple[Path, str, Path | None]]:
    seen: set[Path] = set()
    for workspace_id, workspace_root in catalog.items():
        if workspace_root and (workspace_root / ".ai" / "runs").is_dir():
            run_root = workspace_root / ".ai" / "runs"
            mode = "ATTACHED"
        else:
            run_root = config_home() / "projects" / workspace_id / "runs"
            mode = "EPHEMERAL"
        if not run_root.is_dir():
            continue
        for run_dir in sorted(run_root.iterdir(), key=lambda item: item.name):
            checkpoint = run_dir / "CHECKPOINT.yaml"
            if not run_dir.is_dir() or not checkpoint.is_file() or checkpoint in seen:
                continue
            seen.add(checkpoint)
            yield checkpoint, mode, workspace_root


def _load_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            # A partially-written final line is expected during a live run.
            continue
        if not isinstance(value, dict):
            continue
        event = {
            "sequence": value.get("sequence"),
            "timestamp": value.get("timestamp"),
            "event": safe_text(str(value.get("event") or "UNKNOWN")),
            "status": safe_text(str(value.get("status") or "INFO")),
            "has_evidence": bool(value.get("evidence") or value.get("artifact")),
        }
        events.append(event)
    return events[-MAX_EVENTS:]


def _workspace_health(doc: dict[str, Any], workspace_root: Path | None) -> tuple[str, list[str], dict[str, Any] | None]:
    if workspace_root is None:
        return "UNKNOWN", ["workspace_not_discovered"], None
    if not workspace_root.is_dir():
        return "WORKSPACE_MISSING", ["workspace_removed"], None
    try:
        current = workspace_snapshot(workspace_root)
        fresh, reasons, _ = _freshness(doc, current)
    except (OSError, ValueError, RuntimeError):
        return "UNKNOWN", ["workspace_snapshot_unavailable"], None
    return ("CURRENT" if fresh else "STALE"), reasons, current


def _display_column(status: str, gate: dict[str, Any], current_step: str | None) -> str:
    gate_id = str(gate.get("id") or "").strip()
    gate_status = str(gate.get("status") or "").upper()
    if status == "COMPLETE":
        return "COMPLETE"
    if status == "BLOCKED":
        return "BLOCKED"
    if status == "WAITING" or gate_status in {"WAITING", "BLOCKED"}:
        return f"WAITING: {gate_id}" if gate_id else "WAITING"
    step = str(current_step or "").strip()
    if "janitor" in step.lower() or "validation" in step.lower():
        return "VALIDATION"
    return "ACTIVE" if status == "ACTIVE" else (step or status or "UNKNOWN")


def _project_run(checkpoint: Path, mode: str, workspace_root: Path | None) -> dict[str, Any] | None:
    try:
        doc = load_yaml(checkpoint, {})
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(doc, dict):
        return None
    workspace = doc.get("workspace") or {}
    execution = doc.get("execution") or {}
    gate = doc.get("gate") or {}
    health, reasons, current = _workspace_health(doc, workspace_root)
    current = current or {}
    stored_root = workspace.get("root")
    events = _load_events(checkpoint.parent / "EVENTS.jsonl")
    last_activity = doc.get("updated_at")
    if events and events[-1].get("timestamp"):
        last_activity = events[-1]["timestamp"]
    run_id = str(doc.get("run_id") or checkpoint.parent.name)
    stored_repo = workspace.get("repository_id")
    repository_id = stored_repo or (current.get("repository_id") if current else None)
    return {
        "run_id": run_id,
        "protocol": doc.get("protocol"),
        "status": str(doc.get("status") or "UNKNOWN").upper(),
        "current_step": doc.get("current_step"),
        "display_column": _display_column(str(doc.get("status") or "UNKNOWN").upper(), gate, doc.get("current_step")),
        "execution": {
            "task_id": execution.get("task_id", "UNKNOWN"),
            "role": execution.get("role", "UNKNOWN"),
            "runtime": execution.get("runtime", "UNKNOWN"),
            "isolation_id": execution.get("isolation_id", "UNKNOWN"),
        },
        "gate": {
            "id": gate.get("id", "UNKNOWN"),
            "status": gate.get("status", "UNKNOWN"),
        },
        "workspace": {
            "repository_id": repository_id or "UNKNOWN",
            "workspace_id": workspace.get("workspace_id") or current.get("workspace_id") or "UNKNOWN",
            "branch": workspace.get("branch") or current.get("branch") or "UNKNOWN",
            "revision": workspace.get("revision") or current.get("revision") or "UNKNOWN",
            "mode": mode,
            "health": health,
            "health_reasons": reasons,
        },
        "last_activity": last_activity,
        "events": events,
        "event_count": len(events),
        "checkpoint_version": doc.get("version", 1),
        "checkpoint_available": True,
        "workspace_root_known": bool(stored_root or workspace_root),
    }


def build_projection(project: str | Path, run_id: str | None = None, limit: int = MAX_RUNS) -> dict[str, Any]:
    root = project_root(Path(project))
    identity = repository_identity(root)
    catalog = _workspace_catalog(root)
    runs: list[dict[str, Any]] = []
    for checkpoint, mode, workspace_root in _run_candidates(root, catalog):
        projected = _project_run(checkpoint, mode, workspace_root)
        if projected is None:
            continue
        if projected["workspace"]["repository_id"] not in {identity["repository_id"], "UNKNOWN"}:
            continue
        if run_id and projected["run_id"] != run_id:
            continue
        runs.append(projected)
    runs.sort(key=lambda item: (str(item.get("last_activity") or ""), item["run_id"]), reverse=True)
    runs = runs[: max(1, min(limit, MAX_RUNS))]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "mode": "READ_ONLY",
        "repository": {
            "repository_id": identity["repository_id"],
            "name": root.name,
        },
        "runs": runs,
    }
    payload["snapshot_fingerprint"] = canonical_hash(payload)
    payload["generated_at"] = now()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=False)
    list_parser = sub.add_parser("list")
    list_parser.add_argument("--project", default=os.getcwd())
    list_parser.add_argument("--format", choices=("json", "yaml"), default="yaml")
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--project", default=os.getcwd())
    inspect_parser.add_argument("--run-id", required=True)
    inspect_parser.add_argument("--format", choices=("json", "yaml"), default="yaml")
    args = parser.parse_args()
    command = args.command or "list"
    project = getattr(args, "project", os.getcwd())
    data = build_projection(project, getattr(args, "run_id", None))
    if command == "inspect" and not data["runs"]:
        print("ERROR: run not found", file=sys.stderr)
        return 2
    if getattr(args, "format", "yaml") == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
