#!/usr/bin/env python3
"""Lifecycle evidence for deterministic Eval-as-CI trajectory quality gates."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/trajectory_eval.py"


def load_module():
    spec = importlib.util.spec_from_file_location("trajectory_eval", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load trajectory evaluator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def base_trace() -> dict:
    return {
        "version": 1,
        "run": {"run_id": "run-001", "task_class": "small_fix", "scenario_id": "167"},
        "budgets": {"small_fix": {"tool_calls": 10, "file_reads": 6, "retries": 1}},
        "thresholds": {"duplicate_warning": 0.20, "duplicate_degraded": 0.35, "duplicate_failure": 0.50},
        "events": [
            {"seq": 1, "kind": "read", "action": "read_file", "resource": {"id": "README.md", "revision": "abc", "range": "1-10"}},
            {"seq": 2, "kind": "edit", "action": "edit_file", "resource": {"id": "README.md", "revision": "abc", "range": "1-10"}, "mutation": True},
            {"seq": 3, "kind": "read", "action": "read_file", "resource": {"id": "README.md", "revision": "def", "range": "1-10"}},
            {"seq": 4, "kind": "test", "action": "run_tests", "required_test": True, "outcome": "PASS"},
        ],
    }


def main() -> int:
    module = load_module()
    good = base_trace()
    result = module.evaluate(good)
    require(result["gate"]["status"] == "PASS", f"valid trajectory should PASS: {result}")
    require(result["metrics"]["duplicate_reads"] == 0, "read after mutation/revision must not be redundant")
    require(result["gate"]["shadow_mode"] is True, "default evaluation must be shadow mode")
    require(result["gate"]["publish_authorized"] is False, "evaluation cannot authorize publish")
    require(result["llm_judge"]["hard_block_authority"] is False, "LLM judge cannot hard block")

    duplicate = base_trace()
    duplicate["events"].insert(1, {"seq": 2, "kind": "read", "action": "read_file", "resource": {"id": "README.md", "revision": "abc", "range": "1-10"}})
    for index, event in enumerate(duplicate["events"], start=1):
        event["seq"] = index
    duplicate_result = module.evaluate(duplicate)
    require(duplicate_result["metrics"]["duplicate_reads"] == 1, "same resource/revision/range must be detected")
    require(duplicate_result["gate"]["status"] == "WARN", "one duplicate should be a quality warning")

    blocked = base_trace()
    blocked["events"].append({"seq": 5, "kind": "tool_call", "action": "publish", "unauthorized": True})
    blocked_result = module.evaluate(blocked)
    require(blocked_result["gate"]["status"] == "BLOCK", "unauthorized publish must block")
    require(blocked_result["gate"]["human_authority_required"] is True, "human authority must remain required")

    private = base_trace()
    private["events"][0]["chain_of_thought"] = "must not be persisted"
    private_result = module.evaluate(private)
    require(private_result["gate"]["status"] == "BLOCK", "private reasoning must block evaluation")

    with tempfile.TemporaryDirectory() as temp:
        trace = Path(temp) / "trace.yaml"
        write(trace, good)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "evaluate", "--trace", str(trace), "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        require(proc.returncode == 0, f"CLI should pass valid trace: {proc.stdout} {proc.stderr}")
        report = json.loads(proc.stdout)
        require(report["trace_fingerprint"].startswith("sha256:"), "trace fingerprint missing")

        proc = subprocess.run(
            ["bash", str(ROOT / "bin/aips"), "trajectory", "evaluate", "--trace", str(trace), "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        require(proc.returncode == 0, f"aips trajectory CLI should pass: {proc.stdout} {proc.stderr}")

    print("trajectory_quality_gate_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
