#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import yaml


def fail(message: str) -> None:
    raise RuntimeError(message)


def capture_index(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    captures = result.get("captures") or []
    if not isinstance(captures, list):
        fail("capture result captures must be a list")
    indexed: dict[str, dict[str, Any]] = {}
    for capture in captures:
        if not isinstance(capture, dict) or not capture.get("id"):
            fail("every capture requires an id")
        cid = str(capture["id"])
        if cid in indexed:
            fail(f"duplicate capture id: {cid}")
        indexed[cid] = capture
    return indexed


def metric_value(captures: dict[str, dict[str, Any]], ref: object) -> float | str:
    if not isinstance(ref, dict):
        fail("metric reference must be an object")
    capture_id = str(ref.get("capture") or "")
    metric_name = str(ref.get("metric") or "")
    path = str(ref.get("path") or "")
    if capture_id not in captures or not metric_name or not path:
        fail(f"invalid metric reference: {ref}")

    metric = None
    for item in captures[capture_id].get("metrics") or []:
        if isinstance(item, dict) and item.get("name") == metric_name:
            metric = item.get("values") or {}
            break
    if metric is None:
        fail(f"metric {metric_name!r} missing from capture {capture_id!r}")

    value: Any = metric
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            fail(f"metric path {path!r} missing for {capture_id}:{metric_name}")
        value = value[part]
    if not isinstance(value, (int, float, str)):
        fail(f"metric value must be scalar: {capture_id}:{metric_name}:{path}")
    return value


def numeric(value: float | str) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = value.strip().lower()
    if text.endswith("px"):
        text = text[:-2]
    try:
        return float(text)
    except ValueError as exc:
        raise RuntimeError(f"value is not numeric: {value!r}") from exc


def evaluate_check(captures: dict[str, dict[str, Any]], check: dict[str, Any]) -> dict[str, Any]:
    check_id = str(check.get("id") or "")
    kind = str(check.get("type") or "")
    if not check_id or kind not in {"metric_equal", "metric_not_equal", "capture_present"}:
        fail(f"unsupported or incomplete review check: {check}")

    if kind == "capture_present":
        required = [str(value) for value in (check.get("captures") or [])]
        missing = [value for value in required if value not in captures]
        passed = not missing
        observed: Any = {"required": required, "missing": missing}
    else:
        left = metric_value(captures, check.get("left"))
        right_ref = check.get("right")
        right = metric_value(captures, right_ref) if isinstance(right_ref, dict) else check.get("value")
        if right is None:
            fail(f"{check_id} requires right metric reference or value")
        tolerance = float(check.get("tolerance", 0.01))
        try:
            delta = abs(numeric(left) - numeric(right))
            equal = delta <= tolerance
            observed = {"left": left, "right": right, "delta": delta, "tolerance": tolerance}
        except RuntimeError:
            equal = left == right
            observed = {"left": left, "right": right, "exact": True}
        passed = equal if kind == "metric_equal" else not equal

    return {
        "id": check_id,
        "area": check.get("area") or "rendered consistency",
        "type": kind,
        "result": "PASS" if passed else "FAIL",
        "passed": passed,
        "observed": observed,
        "evidence": check.get("evidence") or [],
    }


def review(capture_result_path: Path, plan_path: Path) -> dict[str, Any]:
    result = yaml.safe_load(capture_result_path.read_text(encoding="utf-8")) or {}
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    if plan.get("version") != 1:
        fail("review plan version must be 1")
    captures = capture_index(result)
    checks = plan.get("checks") or []
    if not isinstance(checks, list) or not checks:
        fail("review plan requires checks")

    evaluated = [evaluate_check(captures, check) for check in checks if isinstance(check, dict)]
    if len(evaluated) != len(checks):
        fail("every review check must be an object")
    passed = all(check["passed"] for check in evaluated)
    return {
        "version": 1,
        "decision": "PASS" if passed else "REQUEST_CHANGES",
        "quality_assessed_by": "visual_review",
        "scope": "objective_rendered_consistency",
        "checks": evaluated,
        "general_visual_quality_inferred": False,
        "note": (
            "This independent deterministic reviewer may decide objective rendered consistency only. "
            "It does not judge creative direction, aesthetics, brand quality, composition or other subjective visual quality."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Independently review objective rendered UI consistency from captured browser metrics.")
    parser.add_argument("capture_result", type=Path)
    parser.add_argument("review_plan", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()

    try:
        result = review(args.capture_result.resolve(), args.review_plan.resolve())
    except Exception as exc:
        if args.format == "json":
            print(json.dumps({"valid": False, "error": str(exc)}, indent=2))
        else:
            print(f"VISUAL CONSISTENCY REVIEW FAILED: {exc}", file=sys.stderr)
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
    if args.format == "json":
        print(json.dumps({"valid": True, **result}, indent=2))
    else:
        print(f"VISUAL CONSISTENCY REVIEW {result['decision']}")
        for check in result["checks"]:
            print(f"- {check['id']}: {check['result']}")
        print(result["note"])
    return 0 if result["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
