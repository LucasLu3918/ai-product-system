#!/usr/bin/env python3
"""Deterministic task scheduler for AIPS structured Task Graphs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import yaml
from review_packet import ALLOWED_SOURCE_CLASSES
from review_evidence import evaluate_evidence

TERMINAL_FAILURE = {"FAILED", "BLOCKED", "STALE", "CANCELLED"}
ALLOWED_STATUS = {"PENDING", "RUNNING", "COMPLETE", *TERMINAL_FAILURE}


class SchedulerError(ValueError):
    pass


ENV_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RESOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def normalize_runtime(isolation: dict[str, Any], task_id: str) -> dict[str, Any]:
    runtime = isolation.get("runtime") or {}
    if not isinstance(runtime, dict):
        raise SchedulerError(f"task {task_id}: isolation.runtime must be a mapping")
    ports = runtime.get("ports") or []
    if not isinstance(ports, list):
        raise SchedulerError(f"task {task_id}: isolation.runtime.ports must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in ports:
        if not isinstance(item, dict):
            raise SchedulerError(f"task {task_id}: each runtime port must be a mapping")
        resource_id = item.get("id")
        if not isinstance(resource_id, str) or not RESOURCE_ID_RE.fullmatch(resource_id):
            raise SchedulerError(f"task {task_id}: runtime port id is invalid")
        if resource_id in seen:
            raise SchedulerError(f"task {task_id}: duplicate runtime port id {resource_id}")
        seen.add(resource_id)
        protocol = item.get("protocol", "tcp")
        if protocol != "tcp":
            raise SchedulerError(f"task {task_id}: only tcp runtime ports are supported")
        preferred = item.get("preferred")
        if preferred is not None and (not isinstance(preferred, int) or preferred < 1024 or preferred > 65535):
            raise SchedulerError(f"task {task_id}: runtime preferred port must be 1024..65535")
        expose_as = item.get("expose_as") or []
        if isinstance(expose_as, str):
            expose_as = [expose_as]
        if not isinstance(expose_as, list) or not all(isinstance(x, str) and ENV_RE.fullmatch(x) for x in expose_as):
            raise SchedulerError(f"task {task_id}: runtime expose_as must contain environment variable names")
        normalized.append(
            {
                "id": resource_id,
                "protocol": "tcp",
                "preferred": preferred,
                "expose_as": sorted(set(expose_as)),
            }
        )
    result: dict[str, Any] = {}
    if normalized:
        result["ports"] = normalized
    return result


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
        read_only = item.get("read_only", False)
        if not isinstance(read_only, bool):
            raise SchedulerError(f"task {task_id}: read_only must be boolean")
        item["read_only"] = read_only
        write_set = item.get("write_set") or []
        if not isinstance(write_set, list) or not all(isinstance(x, str) and x.strip() for x in write_set):
            raise SchedulerError(f"task {task_id}: write_set must be a list of non-empty paths")
        item["write_set"] = sorted(set(x.strip() for x in write_set))
        item["change_boundary"] = normalize_boundaries(item.get("change_boundary"))
        if not item["change_boundary"] and not read_only:
            raise SchedulerError(
                f"task {task_id}: writable or unspecified task requires non-empty change_boundary; "
                "only explicit read_only tasks may omit it"
            )
        if read_only and item["write_set"]:
            raise SchedulerError(f"task {task_id}: read_only task must not declare write_set")
        isolation = item.get("isolation") or {}
        if not isinstance(isolation, dict):
            raise SchedulerError(f"task {task_id}: isolation must be a mapping")
        if read_only and isolation.get("writable") is True:
            raise SchedulerError(f"task {task_id}: read_only task cannot declare writable isolation")
        isolation = dict(isolation)
        isolation["runtime"] = normalize_runtime(isolation, task_id)
        item["isolation"] = isolation
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

    for task_id, task in by_id.items():
        review = task.get("review")
        if review is None:
            continue
        if not isinstance(review, dict):
            raise SchedulerError(f"task {task_id}: review must be a mapping")
        mode = review.get("mode")
        if mode not in {"SELF_CHECK", "INDEPENDENT_REVIEW"}:
            raise SchedulerError(f"task {task_id}: review.mode must be SELF_CHECK or INDEPENDENT_REVIEW")
        review_of = review.get("review_of_task")
        if not isinstance(review_of, str) or review_of not in by_id or review_of == task_id:
            raise SchedulerError(f"task {task_id}: review.review_of_task must name a different existing task")
        if not task["read_only"] or task["write_set"] or task["isolation"].get("writable") is True:
            raise SchedulerError(f"task {task_id}: reviewer must be read_only with no write_set or writable isolation")
        allowed = review.get("allowed_context_classes") or []
        if not isinstance(allowed, list) or any(
            not isinstance(source_class, str) or source_class not in ALLOWED_SOURCE_CLASSES
            for source_class in allowed
        ):
            raise SchedulerError(f"task {task_id}: review.allowed_context_classes contains a non-allowlisted class")
        if len(allowed) != len(set(allowed)):
            raise SchedulerError(f"task {task_id}: review.allowed_context_classes must not contain duplicates")
        if mode == "INDEPENDENT_REVIEW":
            if review_of not in task["dependencies"]:
                raise SchedulerError(f"task {task_id}: independent reviewer must depend on review_of_task")
            if review.get("context_inheritance") != "none":
                raise SchedulerError(f"task {task_id}: independent reviewer requires context_inheritance: none")

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


def validate_completed_reviews(
    by_id: dict[str, dict[str, Any]], state: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    raw_tasks = state.get("tasks") or {}
    review_results: dict[str, dict[str, Any]] = {}
    required_blockers: set[str] = set()
    for task_id, task in by_id.items():
        review = task.get("review")
        if not isinstance(review, dict):
            continue
        raw_review = raw_tasks.get(task_id)
        review_state = raw_review if isinstance(raw_review, dict) else {}
        status = review_state.get("status", raw_review if isinstance(raw_review, str) else "PENDING")
        if status != "COMPLETE":
            review_results[task_id] = {"status": "PENDING", "reason_codes": []}
            continue

        report = review_state.get("review_evidence")
        if not isinstance(report, dict):
            result = {"status": "UNVERIFIED", "reason_codes": ["review_evidence_missing"]}
        elif report.get("mode") != review.get("mode") or report.get("review_of_task") != review.get("review_of_task"):
            result = {"status": "FAILED", "reason_codes": ["review_task_binding_mismatch"]}
        else:
            reviewed_task_state = raw_tasks.get(str(review.get("review_of_task")))
            reviewed_task_state = reviewed_task_state if isinstance(reviewed_task_state, dict) else {}
            implementer_id = reviewed_task_state.get("execution_id")
            reviewer_id = review_state.get("execution_id")
            if not implementer_id or not reviewer_id:
                result = {"status": "UNVERIFIED", "reason_codes": ["execution_identity_unavailable"]}
            elif report.get("implementer_execution_id") != implementer_id or report.get("reviewer_execution_id") != reviewer_id:
                result = {"status": "FAILED", "reason_codes": ["runtime_execution_binding_mismatch"]}
            else:
                candidate = reviewed_task_state.get("candidate")
                expected = candidate if isinstance(candidate, dict) else None
                try:
                    result = evaluate_evidence(report, expected)
                except ValueError:
                    result = {"status": "FAILED", "reason_codes": ["invalid_review_evidence"]}
                declared = set(review.get("allowed_context_classes") or [])
                actual = set(((report.get("context_policy") or {}).get("allowed_classes") or []))
                if actual != declared:
                    result = {"status": "FAILED", "reason_codes": ["declared_context_classes_mismatch"]}

        review_results[task_id] = result
        expected_status = "SELF_CHECK" if review.get("mode") == "SELF_CHECK" else "VERIFIED"
        if review.get("required", False) and result.get("status") != expected_status:
            required_blockers.add(task_id)
    return review_results, required_blockers


def schedule(graph: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    by_id = validate_graph(graph)
    statuses = normalize_state(graph, by_id, state)
    review_statuses, blocked_reviews = validate_completed_reviews(by_id, state)
    for task_id in blocked_reviews:
        statuses[task_id] = "BLOCKED"
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
        review = task.get("review")
        if isinstance(review, dict) and review.get("mode") == "INDEPENDENT_REVIEW":
            reviewed_state = (state.get("tasks") or {}).get(str(review.get("review_of_task")))
            reviewed_state = reviewed_state if isinstance(reviewed_state, dict) else {}
            if not isinstance(reviewed_state.get("execution_id"), str) or not reviewed_state["execution_id"].strip():
                blocked[task_id] = "implementer_execution_id_unverified"
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
        "runtime_requests": {
            task_id: by_id[task_id]["isolation"]["runtime"]
            for task_id in dispatch
            if by_id[task_id]["isolation"].get("runtime")
        },
        "deferred": dict(sorted(deferred.items())),
        "blocked": dict(sorted(blocked.items())),
        "complete": sorted(task_id for task_id, status in statuses.items() if status == "COMPLETE"),
        "failed": sorted(task_id for task_id, status in statuses.items() if status in TERMINAL_FAILURE),
        "review_statuses": {task_id: review_statuses[task_id] for task_id in sorted(review_statuses)},
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
