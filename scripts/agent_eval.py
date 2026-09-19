#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_KEYS = {
    "analysis",
    "chain_of_thought",
    "chain-of-thought",
    "cot",
    "private_reasoning",
    "reasoning_trace",
    "scratchpad",
    "thoughts",
}
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:password|api[_-]?key|secret|token)\s*[:=]\s*[^\s,;]{8,}"),
)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected mapping")
    return data


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    return value


def fingerprint(doc: dict[str, Any]) -> str:
    payload = json.dumps(canonicalize(doc), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_path(doc: dict[str, Any], path: str) -> Any:
    current: Any = doc
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(path)
        current = current[part]
    return current


def private_reasoning_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).strip().lower() in FORBIDDEN_KEYS:
                found.append(path)
            found.extend(private_reasoning_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(private_reasoning_paths(child, f"{prefix}[{index}]"))
    return found


def secret_findings(value: Any, prefix: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            findings.extend(secret_findings(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(secret_findings(child, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                findings.append(prefix or "<root>")
                break
    return findings


def validate_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if case.get("version") != 1:
        errors.append("case.version must be 1")
    if not str(case.get("id") or ""):
        errors.append("case.id is required")
    if not re.fullmatch(r"\d{3}", str(case.get("scenario_id") or "")):
        errors.append("case.scenario_id must be a 3-digit string")
    input_doc = case.get("input") or {}
    if not isinstance(input_doc, dict) or not str(input_doc.get("prompt") or "").strip():
        errors.append("case.input.prompt is required")
    rubric = case.get("rubric") or {}
    if not isinstance(rubric, dict):
        errors.append("case.rubric must be a mapping")
        return errors
    for section in ("equals", "contains", "excludes", "set_equals"):
        value = rubric.get(section, {})
        if value is not None and not isinstance(value, dict):
            errors.append(f"case.rubric.{section} must be a mapping")
    nonempty = rubric.get("nonempty", [])
    if nonempty is not None and not isinstance(nonempty, list):
        errors.append("case.rubric.nonempty must be a list")
    return errors


def validate_result(case: dict[str, Any], result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("version") != 1:
        errors.append("result.version must be 1")
    if result.get("case_id") != case.get("id"):
        errors.append("result.case_id does not match case.id")
    if str(result.get("scenario_id") or "") != str(case.get("scenario_id") or ""):
        errors.append("result.scenario_id does not match case.scenario_id")
    expected_fp = fingerprint(case)
    if result.get("case_fingerprint") != expected_fp:
        errors.append("result.case_fingerprint is missing or stale")
    execution = result.get("execution") or {}
    if not isinstance(execution, dict):
        errors.append("result.execution must be a mapping")
    else:
        for key in ("provider", "model", "runtime", "executed_at"):
            if not str(execution.get(key) or "").strip():
                errors.append(f"result.execution.{key} is required")
    response = result.get("response")
    if not isinstance(response, dict):
        errors.append("result.response must be a mapping")
    private = private_reasoning_paths(result)
    if private:
        errors.append("private reasoning fields are prohibited: " + ", ".join(private))
    secret_paths = secret_findings(result)
    if secret_paths:
        errors.append("secret-like values are prohibited in recorded Agent Eval results: " + ", ".join(secret_paths))
    return errors


def score(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    errors = validate_case(case) + validate_result(case, result)
    checks: list[dict[str, Any]] = []
    response_doc = {"response": result.get("response") or {}}
    rubric = case.get("rubric") or {}

    def record(kind: str, path: str, passed: bool, detail: str) -> None:
        checks.append({"type": kind, "path": path, "status": "PASS" if passed else "FAIL", "detail": detail})

    for path, expected in (rubric.get("equals") or {}).items():
        try:
            actual = get_path(response_doc, path)
            passed = actual == expected
            record("equals", path, passed, "matched" if passed else f"expected {expected!r}, got {actual!r}")
        except KeyError:
            record("equals", path, False, "path missing")

    for path, expected_items in (rubric.get("contains") or {}).items():
        try:
            actual = get_path(response_doc, path)
            if not isinstance(actual, list):
                record("contains", path, False, "actual value is not a list")
                continue
            missing = [item for item in expected_items if item not in actual]
            record("contains", path, not missing, "matched" if not missing else f"missing {missing!r}")
        except KeyError:
            record("contains", path, False, "path missing")

    for path, excluded_items in (rubric.get("excludes") or {}).items():
        try:
            actual = get_path(response_doc, path)
            if not isinstance(actual, list):
                record("excludes", path, False, "actual value is not a list")
                continue
            present = [item for item in excluded_items if item in actual]
            record("excludes", path, not present, "matched" if not present else f"unexpected {present!r}")
        except KeyError:
            record("excludes", path, False, "path missing")

    for path, expected_items in (rubric.get("set_equals") or {}).items():
        try:
            actual = get_path(response_doc, path)
            if not isinstance(actual, list):
                record("set_equals", path, False, "actual value is not a list")
                continue
            passed = sorted(map(str, actual)) == sorted(map(str, expected_items))
            record("set_equals", path, passed, "matched" if passed else f"expected set {expected_items!r}, got {actual!r}")
        except KeyError:
            record("set_equals", path, False, "path missing")

    for path in (rubric.get("nonempty") or []):
        try:
            actual = get_path(response_doc, path)
            passed = actual is not None and actual != "" and actual != [] and actual != {}
            record("nonempty", path, passed, "present" if passed else "empty")
        except KeyError:
            record("nonempty", path, False, "path missing")

    failed = [item for item in checks if item["status"] != "PASS"]
    status = "PASS" if not errors and not failed else "FAIL"
    return {
        "status": status,
        "case_id": case.get("id"),
        "scenario_id": str(case.get("scenario_id") or ""),
        "case_fingerprint": fingerprint(case),
        "errors": errors,
        "checks": checks,
    }



def response_fingerprint(response: dict[str, Any]) -> str:
    """Fingerprint observable response data without persisting response text in the report."""
    return fingerprint({"response": response})


def consistency(
    case: dict[str, Any],
    named_results: list[tuple[str, dict[str, Any]]],
    *,
    min_repetitions: int = 5,
    min_pass_rate: float = 1.0,
) -> dict[str, Any]:
    """Measure repeatability across independently recorded observable Agent Eval results."""
    errors = validate_case(case)
    if min_repetitions < 2:
        errors.append("min_repetitions must be >= 2")
    if not 0.0 <= min_pass_rate <= 1.0:
        errors.append("min_pass_rate must be between 0 and 1")

    passed = 0
    failed = 0
    valid = 0
    response_counts: dict[str, int] = {}
    runs: list[dict[str, Any]] = []

    for source, result in named_results:
        validation_errors = validate_result(case, result)
        response_fp: str | None = None
        if validation_errors:
            errors.extend(f"{source}: {message}" for message in validation_errors)
            run_status = "INVALID"
        else:
            valid += 1
            scored = score(case, result)
            run_status = scored["status"]
            if run_status == "PASS":
                passed += 1
            else:
                failed += 1
            response = result.get("response") or {}
            if isinstance(response, dict):
                response_fp = response_fingerprint(response)
                response_counts[response_fp] = response_counts.get(response_fp, 0) + 1

        runs.append({"source": source, "status": run_status, "response_fingerprint": response_fp})

    repetitions = len(named_results)
    if repetitions < min_repetitions:
        errors.append(f"insufficient repetitions: required {min_repetitions}, got {repetitions}")

    pass_rate = (passed / repetitions) if repetitions else 0.0
    if pass_rate + 1e-12 < min_pass_rate:
        errors.append(f"pass rate below threshold: required {min_pass_rate:.3f}, got {pass_rate:.3f}")

    outcome_consistency = (max(passed, failed) / valid) if valid else 0.0
    response_repeatability = (max(response_counts.values()) / valid) if valid and response_counts else 0.0

    return {
        "status": "PASS" if not errors else "FAIL",
        "case_id": case.get("id"),
        "scenario_id": str(case.get("scenario_id") or ""),
        "case_fingerprint": fingerprint(case),
        "policy": {"min_repetitions": min_repetitions, "min_pass_rate": min_pass_rate},
        "summary": {
            "repetitions": repetitions,
            "valid_results": valid,
            "invalid_results": repetitions - valid,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(pass_rate, 6),
            "outcome_consistency": round(outcome_consistency, 6),
            "unique_observable_responses": len(response_counts),
            "response_repeatability": round(response_repeatability, 6),
        },
        "errors": errors,
        "runs": runs,
    }


def case_files(directory: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in sorted(directory.glob("*.yaml")):
        doc = load_yaml(path)
        case_id = str(doc.get("id") or path.stem)
        if case_id in result:
            raise ValueError(f"duplicate Agent Eval case id: {case_id}")
        result[case_id] = path
    return result


def result_files(directory: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in sorted(directory.glob("*.yaml")):
        doc = load_yaml(path)
        case_id = str(doc.get("case_id") or path.stem)
        if case_id in result:
            raise ValueError(f"duplicate Agent Eval result case_id: {case_id}")
        result[case_id] = path
    return result


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def analyze(cases_dir: Path, results_dir: Path) -> dict[str, Any]:
    cases = case_files(cases_dir)
    results = result_files(results_dir)
    errors: list[str] = []
    items: list[dict[str, Any]] = []

    for case_id, case_path in cases.items():
        result_path = results.get(case_id)
        if result_path is None:
            errors.append(f"missing Agent Eval result for case: {case_id}")
            continue
        case = load_yaml(case_path)
        result = load_yaml(result_path)
        scored = score(case, result)
        scored["case_path"] = display_path(case_path)
        scored["result_path"] = display_path(result_path)
        items.append(scored)
        if scored["status"] != "PASS":
            errors.append(f"Agent Eval case failed: {case_id}")

    for orphan in sorted(set(results) - set(cases)):
        errors.append(f"orphan Agent Eval result: {orphan}")

    passed = sum(1 for item in items if item["status"] == "PASS")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "summary": {
            "cases": len(cases),
            "results": len(results),
            "passed": passed,
            "failed": len(items) - passed,
            "missing_results": len(set(cases) - set(results)),
            "orphan_results": len(set(results) - set(cases)),
        },
        "cases": items,
    }


def emit(data: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())


def main() -> int:
    parser = argparse.ArgumentParser(description="AIPS provider-neutral Agent Eval recorder/scorer")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("check", "report"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--cases-dir", default=str(ROOT / "tests" / "agent_eval" / "cases"))
        cmd.add_argument("--results-dir", default=str(ROOT / "tests" / "agent_eval" / "results"))
        cmd.add_argument("--format", choices=["yaml", "json"], default="yaml")

    fp = sub.add_parser("fingerprint")
    fp.add_argument("--case", required=True)

    sc = sub.add_parser("score")
    sc.add_argument("--case", required=True)
    sc.add_argument("--result", required=True)
    sc.add_argument("--format", choices=["yaml", "json"], default="yaml")

    co = sub.add_parser("consistency")
    co.add_argument("--case", required=True)
    co.add_argument("--results-dir", required=True)
    co.add_argument("--min-repetitions", type=int, default=5)
    co.add_argument("--min-pass-rate", type=float, default=1.0)
    co.add_argument("--format", choices=["yaml", "json"], default="yaml")

    args = parser.parse_args()
    try:
        if args.command == "fingerprint":
            print(fingerprint(load_yaml(Path(args.case))))
            return 0
        if args.command == "score":
            data = score(load_yaml(Path(args.case)), load_yaml(Path(args.result)))
            emit(data, args.format)
            return 0 if data["status"] == "PASS" else 2
        if args.command == "consistency":
            case = load_yaml(Path(args.case))
            results_dir = Path(args.results_dir).resolve()
            named_results = [(display_path(path), load_yaml(path)) for path in sorted(results_dir.glob("*.yaml"))]
            data = consistency(case, named_results, min_repetitions=args.min_repetitions, min_pass_rate=args.min_pass_rate)
            emit(data, args.format)
            return 0 if data["status"] == "PASS" else 2

        data = analyze(Path(args.cases_dir).resolve(), Path(args.results_dir).resolve())
        emit(data, args.format)
        if args.command == "report":
            return 0
        return 0 if data["status"] == "PASS" else 2
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
