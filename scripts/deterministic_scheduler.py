#!/usr/bin/env python3
"""Deterministic task scheduler for AIPS structured Task Graphs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

TERMINAL_FAILURE = {"FAILED", "BLOCKED", "STALE", "CANCELLED"}
ALLOWED_STATUS = {"PENDING", "RUNNING", "COMPLETE", *TERMINAL_FAILURE}


class SchedulerError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SchedulerError(f"expected mapping: {path}")
    return data


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_boundaries(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list) or not all(isinstance(x, str) and x.strip() for x in raw):
        raise SchedulerError("change_boundary must be a non-empty string or list of strings")
    return tuple(sorted({x.strip().strip("/") for x in raw}))


def boundary_conflict(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    for a in left:
        for b in right:
            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                return True
    return False


def validate_graph(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if graph.get("version") != 1:
        raise SchedulerError("task graph version must be 1")
    tasks = graph.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise SchedulerError("task graph tasks must be a non-empty list")

    by_id: dict[str, dict[str, Any]] = {}
    for item in tasks:
        if not isinstance(item, dict):
            raise SchedulerError("each task must be a mapping")
        task_id = item.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise SchedulerError("each task requires id")
        if task_id in by_id:
            raise SchedulerError(f"duplicate task id: {task_id}")
        item = dict(item)
        item["change_boundary"] = normalize_boundaries(item.get("change_boundary"))
        deps = item.get("dependencies") or []
        if not isinstance(deps, list) or not all(isinstance(x, str) for x in deps):
            raise SchedulerError(f"task {task_id}: dependencies must be a list of ids")
        item["dependencies"] = sorted(set(deps))
        order = item.get("order", 100)
        if not isinstance(order, int):
            raise SchedulerError(f"task {task_id}: order must be integer")
        item["order"] = order
        by_id[task_id] = item

    for task_id, task in by_id.items():
        for dep in task["dependencies"]:
            if dep not in by_id:
                raise SchedulerError(f"task {task_id}: unknown dependency {dep}")
            if dep == task_id:
                raise SchedulerError(f"task {task_id}: self dependency")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise SchedulerError(f"dependency cycle includes {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dep in by_id[task_id]["dependencies"]:
            visit(dep)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in sorted(by_id):
        visit(task_id)
    return by_id


def normalize_state(graph: dict[str, Any], by_id: dict[str, dict[str, Any]], state: dict[str, Any]) -> dict[str, str]:
    graph_plan_id = graph.get("plan_id")
    state_plan_id = state.get("plan_id")
    if state_plan_id not in (None, graph_plan_id):
        raise SchedulerError("state plan_id does not match task graph")
    raw = state.get("tasks") or {}
    if not isinstance(raw, dict):
        raise SchedulerError("state.tasks must be a mapping")
    result: dict[str, str] = {}
    for task_id in by_id:
        status = raw.get(task_id, "PENDING")
        if isinstance(status, dict):
            status = status.get("status", "PENDING")
        if status not in ALLOWED_STATUS:
            raise SchedulerError(f"task {task_id}: unsupported status {status!r}")
        result[task_id] = status
    unknown = sorted(set(raw) - set(by_id))
    if unknown:
        raise SchedulerError(f"state contains unknown tasks: {', '.join(unknown)}")
    return result


def schedule(graph: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    by_id = validate_graph(graph)
    statuses = normalize_state(graph, by_id, state)
    max_parallel = graph.get("max_parallel", 1)
    if not isinstance(max_parallel, int) or max_parallel < 1:
        raise SchedulerError("max_parallel must be >= 1")

    running = [task_id for task_id, status in statuses.items() if status == "RUNNING"]
    for task_id in running:
        incomplete = [dep for dep in by_id[task_id]["dependencies"] if statuses[dep] != "COMPLETE"]
        if incomplete:
            raise SchedulerError(f"running task {task_id} has incomplete dependencies: {','.join(sorted(incomplete))}")
    active_boundaries = [by_id[task_id]["change_boundary"] for task_id in running]
    for index, boundary in enumerate(active_boundaries):
        if any(boundary_conflict(boundary, other) for other in active_boundaries[index + 1 :]):
            raise SchedulerError("running state contains overlapping Change Boundary locks")
    available_slots = max(0, max_parallel - len(running))

    blocked: dict[str, str] = {}
    ready: list[str] = []
    for task_id, task in by_id.items():
        if statuses[task_id] != "PENDING":
            continue
        dep_states = {dep: statuses[dep] for dep in task["dependencies"]}
        failed = sorted(dep for dep, status in dep_states.items() if status in TERMINAL_FAILURE)
        if failed:
            blocked[task_id] = "failed_dependency:" + ",".join(failed)
            continue
        incomplete = sorted(dep for dep, status in dep_states.items() if status != "COMPLETE")
        if incomplete:
            blocked[task_id] = "waiting_dependency:" + ",".join(incomplete)
            continue
        ready.append(task_id)

    ready.sort(key=lambda task_id: (by_id[task_id]["order"], task_id))
    dispatch: list[str] = []
    deferred: dict[str, str] = {}
    selected_boundaries = list(active_boundaries)
    for task_id in ready:
        if len(dispatch) >= available_slots:
            deferred[task_id] = "parallel_limit"
            continue
        boundary = by_id[task_id]["change_boundary"]
        if any(boundary_conflict(boundary, other) for other in selected_boundaries):
            deferred[task_id] = "change_boundary_lock"
            continue
        dispatch.append(task_id)
        selected_boundaries.append(boundary)

    result = {
        "version": 1,
        "plan_id": graph.get("plan_id"),
        "base_revision": graph.get("base_revision"),
        "graph_fingerprint": canonical_hash(graph),
        "state_fingerprint": canonical_hash({"plan_id": graph.get("plan_id"), "tasks": statuses}),
        "max_parallel": max_parallel,
        "running": sorted(running),
        "dispatch": dispatch,
        "deferred": dict(sorted(deferred.items())),
        "blocked": dict(sorted(blocked.items())),
        "complete": sorted(task_id for task_id, status in statuses.items() if status == "COMPLETE"),
        "failed": sorted(task_id for task_id, status in statuses.items() if status in TERMINAL_FAILURE),
    }
    result["decision_fingerprint"] = canonical_hash(result)
    return result


def dump(value: Any, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(value, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        graph = load_yaml(args.graph)
        state = load_yaml(args.state) if args.state else {"plan_id": graph.get("plan_id"), "tasks": {}}
        result = schedule(graph, state)
    except (OSError, yaml.YAMLError, SchedulerError) as exc:
        print(f"SCHEDULER BLOCKED: {exc}")
        return 2

    rendered = dump(result, args.format)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
