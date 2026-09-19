#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
AGENT_EVAL = ROOT / "scripts" / "agent_eval.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module():
    spec = importlib.util.spec_from_file_location("aips_agent_eval", AGENT_EVAL)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load agent_eval.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def base_case() -> dict:
    return {
        "version": 1,
        "id": "test-case",
        "scenario_id": "999",
        "description": "framework fixture",
        "input": {"prompt": "Choose the safe action.", "context": {"material": True}},
        "rubric": {
            "equals": {
                "response.status": "NEEDS_APPROVAL",
                "response.allowed": False,
            },
            "contains": {"response.actions": ["stop", "request_approval"]},
            "excludes": {"response.actions": ["implement"]},
            "set_equals": {"response.reviewers": ["architect", "security"]},
            "nonempty": ["response.summary"],
        },
    }


def base_result(module, case: dict, provider: str = "provider-x") -> dict:
    return {
        "version": 1,
        "case_id": case["id"],
        "scenario_id": case["scenario_id"],
        "case_fingerprint": module.fingerprint(case),
        "execution": {
            "provider": provider,
            "model": "model-y",
            "runtime": "runtime-z",
            "executed_at": "2026-09-17",
        },
        "response": {
            "status": "NEEDS_APPROVAL",
            "allowed": False,
            "actions": ["stop", "request_approval"],
            "reviewers": ["security", "architect"],
            "summary": "Observable decision only.",
        },
    }


def main() -> int:
    module = load_module()
    case = base_case()

    reordered = {
        "rubric": case["rubric"],
        "scenario_id": case["scenario_id"],
        "input": case["input"],
        "description": case["description"],
        "id": case["id"],
        "version": case["version"],
    }
    require(module.fingerprint(case) == module.fingerprint(reordered), "fingerprint must be deterministic across key ordering")

    result = base_result(module, case)
    scored = module.score(case, result)
    require(scored["status"] == "PASS", f"valid provider-neutral result should PASS: {scored}")

    bad = base_result(module, case)
    bad["response"]["status"] = "READY"
    bad_score = module.score(case, bad)
    require(bad_score["status"] == "FAIL", "rubric mismatch must fail scoring")

    private = base_result(module, case)
    private["response"]["chain_of_thought"] = "hidden reasoning must never be persisted"
    private_score = module.score(case, private)
    require(private_score["status"] == "FAIL", "private reasoning fields must be rejected")
    require(any("private reasoning" in e for e in private_score["errors"]), "private reasoning failure reason missing")

    secret = base_result(module, case)
    secret["response"]["summary"] = "token=" + ("A" * 32)
    secret_score = module.score(case, secret)
    require(secret_score["status"] == "FAIL", "secret-like recorded value must be rejected")

    changed_case = base_case()
    changed_case["input"]["context"]["material"] = False
    stale_score = module.score(changed_case, result)
    require(stale_score["status"] == "FAIL", "case mutation must stale recorded result fingerprint")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cases = root / "cases"
        results = root / "results"
        write_yaml(cases / "test-case.yaml", case)
        write_yaml(results / "test-case.yaml", result)

        checked = subprocess.run(
            [
                sys.executable,
                str(AGENT_EVAL),
                "check",
                "--cases-dir",
                str(cases),
                "--results-dir",
                str(results),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        require(checked.returncode == 0, f"valid Agent Eval lifecycle must PASS: {checked.stdout} {checked.stderr}")
        checked_doc = json.loads(checked.stdout)
        require(checked_doc["summary"]["passed"] == 1, "Agent Eval PASS count mismatch")

        (results / "test-case.yaml").unlink()
        missing = subprocess.run(
            [
                sys.executable,
                str(AGENT_EVAL),
                "check",
                "--cases-dir",
                str(cases),
                "--results-dir",
                str(results),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        require(missing.returncode != 0, "missing result must fail Agent Eval check")

        orphan = base_result(module, case)
        orphan["case_id"] = "orphan"
        write_yaml(results / "orphan.yaml", orphan)
        orphan_check = subprocess.run(
            [
                sys.executable,
                str(AGENT_EVAL),
                "check",
                "--cases-dir",
                str(cases),
                "--results-dir",
                str(results),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        require(orphan_check.returncode != 0, "orphan result must fail Agent Eval check")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        case_path = root / "repeatability-case.yaml"
        repetitions = root / "repetitions"
        write_yaml(case_path, case)
        for index in range(5):
            repeated = base_result(module, case, provider=f"provider-{index % 2}")
            repeated["execution"]["executed_at"] = f"2026-09-19T00:00:0{index}Z"
            repeated["response"]["summary"] = f"Observable decision run {index}."
            write_yaml(repetitions / f"run-{index}.yaml", repeated)

        consistent = subprocess.run([
            sys.executable, str(AGENT_EVAL), "consistency", "--case", str(case_path),
            "--results-dir", str(repetitions), "--min-repetitions", "5", "--min-pass-rate", "1.0", "--format", "json",
        ], capture_output=True, text=True)
        require(consistent.returncode == 0, f"repeatability evidence should PASS: {consistent.stdout} {consistent.stderr}")
        consistent_doc = json.loads(consistent.stdout)
        require(consistent_doc["summary"]["repetitions"] == 5, "repeatability repetition count mismatch")
        require(consistent_doc["summary"]["passed"] == 5, "repeatability PASS count mismatch")
        require(consistent_doc["summary"]["pass_rate"] == 1.0, "repeatability pass rate mismatch")
        require(consistent_doc["summary"]["unique_observable_responses"] == 5, "observable response diversity must remain visible")
        require(consistent_doc["summary"]["response_repeatability"] == 0.2, "exact response repeatability must be measured separately from rubric success")

        degraded = yaml.safe_load((repetitions / "run-4.yaml").read_text(encoding="utf-8"))
        degraded["response"]["status"] = "READY"
        write_yaml(repetitions / "run-4.yaml", degraded)
        strict = subprocess.run([
            sys.executable, str(AGENT_EVAL), "consistency", "--case", str(case_path),
            "--results-dir", str(repetitions), "--min-repetitions", "5", "--min-pass-rate", "1.0", "--format", "json",
        ], capture_output=True, text=True)
        require(strict.returncode != 0, "strict repeatability policy must fail a 4/5 outcome")
        require(json.loads(strict.stdout)["summary"]["pass_rate"] == 0.8, "degraded repeatability pass rate mismatch")

        relaxed = subprocess.run([
            "bash", str(ROOT / "bin" / "aips"), "conformance", "agent-eval", "consistency",
            "--case", str(case_path), "--results-dir", str(repetitions), "--min-repetitions", "5",
            "--min-pass-rate", "0.8", "--format", "json",
        ], capture_output=True, text=True)
        require(relaxed.returncode == 0, f"configured 80% repeatability threshold should PASS: {relaxed.stdout} {relaxed.stderr}")

        stale = yaml.safe_load((repetitions / "run-3.yaml").read_text(encoding="utf-8"))
        stale["case_fingerprint"] = "sha256:" + ("0" * 64)
        write_yaml(repetitions / "run-3.yaml", stale)
        invalid = subprocess.run([
            sys.executable, str(AGENT_EVAL), "consistency", "--case", str(case_path),
            "--results-dir", str(repetitions), "--min-repetitions", "5", "--min-pass-rate", "0.8", "--format", "json",
        ], capture_output=True, text=True)
        require(invalid.returncode != 0, "stale repetition evidence must fail regardless of pass-rate threshold")
        require(json.loads(invalid.stdout)["summary"]["invalid_results"] == 1, "stale repetition must be reported as invalid")

    print("agent_eval_framework evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
