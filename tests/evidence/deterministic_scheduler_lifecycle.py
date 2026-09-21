#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "deterministic_scheduler.py"


def run(graph: dict, state: dict) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        graph_path = tmp / "graph.yaml"
        state_path = tmp / "state.yaml"
        graph_path.write_text(yaml.safe_dump(graph, sort_keys=False), encoding="utf-8")
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        proc = subprocess.run(
            ["python3", str(SCRIPT), "--graph", str(graph_path), "--state", str(state_path), "--format", "json"],
            text=True,
            capture_output=True,
        )
        payload = json.loads(proc.stdout) if proc.returncode == 0 else {}
        return proc.returncode, payload


def main() -> int:
    graph = {
        "version": 1,
        "plan_id": "plan-135",
        "base_revision": "abc123",
        "max_parallel": 3,
        "tasks": [
            {"id": "api", "order": 10, "dependencies": [], "change_boundary": ["modules/api"]},
            {"id": "billing", "order": 20, "dependencies": [], "change_boundary": ["modules/billing"]},
            {"id": "api-tests", "order": 30, "dependencies": ["api"], "change_boundary": ["modules/api/tests"]},
            {"id": "api-docs", "order": 40, "dependencies": [], "change_boundary": ["modules/api/docs"]},
        ],
    }
    state = {"plan_id": "plan-135", "tasks": {}}
    rc1, first = run(graph, state)
    rc2, second = run(graph, state)
    assert rc1 == rc2 == 0
    assert first == second, "same graph/state must produce byte-equivalent semantic decision"
    assert first["dispatch"] == ["api", "billing"], first
    assert first["deferred"]["api-docs"] == "change_boundary_lock"
    assert first["blocked"]["api-tests"] == "waiting_dependency:api"

    state2 = {"plan_id": "plan-135", "tasks": {"api": "COMPLETE", "billing": "RUNNING"}}
    rc3, resumed = run(graph, state2)
    assert rc3 == 0
    assert "api-tests" in resumed["dispatch"]
    assert resumed["running"] == ["billing"]

    cyclic = {
        "version": 1,
        "plan_id": "cycle",
        "max_parallel": 2,
        "tasks": [
            {"id": "a", "dependencies": ["b"], "change_boundary": ["a"]},
            {"id": "b", "dependencies": ["a"], "change_boundary": ["b"]},
        ],
    }
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        p = tmp / "graph.yaml"
        p.write_text(yaml.safe_dump(cyclic), encoding="utf-8")
        proc = subprocess.run(["python3", str(SCRIPT), "--graph", str(p)], text=True, capture_output=True)
        assert proc.returncode == 2
        assert "dependency cycle" in proc.stdout

    # A task that may write is fail-closed without an explicit Change Boundary.
    writable_without_boundary = {
        "version": 1,
        "plan_id": "missing-boundary",
        "max_parallel": 1,
        "tasks": [
            {"id": "writer", "dependencies": [], "write_set": ["modules/api/**"]},
        ],
    }
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        p = tmp / "graph.yaml"
        p.write_text(yaml.safe_dump(writable_without_boundary), encoding="utf-8")
        proc = subprocess.run(["python3", str(SCRIPT), "--graph", str(p)], text=True, capture_output=True)
        assert proc.returncode == 2
        assert "requires non-empty change_boundary" in proc.stdout

    # An explicitly read-only task may omit Change Boundary because it owns no writer lock.
    read_only_graph = {
        "version": 1,
        "plan_id": "read-only",
        "max_parallel": 1,
        "tasks": [
            {"id": "inspect", "dependencies": [], "read_only": True, "write_set": [], "change_boundary": []},
        ],
    }
    rc_read, read_decision = run(read_only_graph, {"plan_id": "read-only", "tasks": {}})
    assert rc_read == 0
    assert read_decision["dispatch"] == ["inspect"]

    # read_only is a contract, not a bypass for a declared write set.
    invalid_read_only = {
        "version": 1,
        "plan_id": "invalid-read-only",
        "max_parallel": 1,
        "tasks": [
            {"id": "bad", "dependencies": [], "read_only": True, "write_set": ["modules/api/**"], "change_boundary": []},
        ],
    }
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        p = tmp / "graph.yaml"
        p.write_text(yaml.safe_dump(invalid_read_only), encoding="utf-8")
        proc = subprocess.run(["python3", str(SCRIPT), "--graph", str(p)], text=True, capture_output=True)
        assert proc.returncode == 2
        assert "read_only task must not declare write_set" in proc.stdout

    runtime_graph = {
        "version": 1,
        "plan_id": "runtime-ports",
        "max_parallel": 2,
        "tasks": [
            {
                "id": "frontend-a",
                "dependencies": [],
                "change_boundary": ["apps/a"],
                "isolation": {
                    "mode": "worktree",
                    "required": True,
                    "runtime": {
                        "ports": [
                            {"id": "dev", "protocol": "tcp", "preferred": 3000, "expose_as": ["PORT"]}
                        ]
                    },
                },
            },
            {
                "id": "frontend-b",
                "dependencies": [],
                "change_boundary": ["apps/b"],
                "isolation": {
                    "mode": "worktree",
                    "required": True,
                    "runtime": {
                        "ports": [
                            {"id": "dev", "protocol": "tcp", "preferred": 3000, "expose_as": ["PORT"]}
                        ]
                    },
                },
            },
        ],
    }
    rc_runtime, runtime_decision = run(runtime_graph, {"plan_id": "runtime-ports", "tasks": {}})
    assert rc_runtime == 0
    assert runtime_decision["dispatch"] == ["frontend-a", "frontend-b"]
    assert runtime_decision["runtime_requests"]["frontend-a"]["ports"][0]["id"] == "dev"
    assert runtime_decision["runtime_requests"]["frontend-a"]["ports"][0]["expose_as"] == ["PORT"]

    invalid_runtime = {
        "version": 1,
        "plan_id": "invalid-runtime",
        "max_parallel": 1,
        "tasks": [
            {
                "id": "frontend",
                "dependencies": [],
                "change_boundary": ["apps/frontend"],
                "isolation": {"runtime": {"ports": [{"id": "dev", "protocol": "udp"}]}},
            }
        ],
    }
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        p = tmp / "graph.yaml"
        p.write_text(yaml.safe_dump(invalid_runtime), encoding="utf-8")
        proc = subprocess.run(["python3", str(SCRIPT), "--graph", str(p)], text=True, capture_output=True)
        assert proc.returncode == 2
        assert "only tcp runtime ports are supported" in proc.stdout

    print("deterministic scheduler lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
