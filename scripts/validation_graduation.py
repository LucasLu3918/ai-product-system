#!/usr/bin/env python3
"""Evaluate full-run shadow evidence; never enables selective execution."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validation_shadow_plan as shadow


class GraduationError(ValueError):
    pass


def _iso_date(value: Any, field: str, errors: list[str]) -> date | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{field} is required")
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        errors.append(f"{field} must be an ISO-8601 date or timestamp")
        return None


def deterministic_full_audit(head_sha: str, modulo: int) -> bool:
    digest = hashlib.sha256(head_sha.encode("ascii")).hexdigest()
    return int(digest[:8], 16) % modulo == 0


def evaluate(
    config: dict[str, Any], scope_config: dict[str, Any], dataset: dict[str, Any]
) -> dict[str, Any]:
    errors: list[str] = []
    graduation = config.get("graduation") or {}
    execution = config.get("execution") or {}
    if config.get("version") != 1 or config.get("mode") != "full_run_shadow":
        errors.append("graduation policy must be version 1 full_run_shadow")
    if execution.get("selective_execution_enabled") is not False:
        errors.append("selective execution must remain disabled during graduation evaluation")
    if execution.get("automatic_activation_authorized") is not False:
        errors.append("automatic activation must remain unauthorized")
    if execution.get("human_decision_required") is not True:
        errors.append("graduation requires an explicit Human decision")

    start = _iso_date(dataset.get("window_start"), "window_start", errors)
    end = _iso_date(dataset.get("window_end"), "window_end", errors)
    window_days = (end - start).days + 1 if start and end and end >= start else 0
    if start and end and end < start:
        errors.append("window_end must be on or after window_start")
    minimum_days = int(graduation.get("minimum_observation_days") or 30)
    if window_days < minimum_days:
        errors.append(f"observation window is {window_days} days; {minimum_days} required")
    if graduation.get("require_complete_artifact_history") is True and dataset.get("artifact_history_complete") is not True:
        errors.append("artifact history is incomplete or unverified")

    records = dataset.get("records")
    if not isinstance(records, list):
        records = []
        errors.append("records must be a list")
    expected_modules = [spec.module for spec in shadow.VALIDATORS]
    pull_requests: set[int] = set()
    false_negatives: list[dict[str, Any]] = []
    malformed_records: list[int] = []
    audit_count = 0
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            malformed_records.append(index)
            continue
        required = ("pull_request", "base_sha", "head_sha", "timestamp", "change_class", "changed_paths", "failed_modules", "actual_modules_run", "full_validation_run")
        if any(key not in record for key in required):
            malformed_records.append(index)
            continue
        pr = record.get("pull_request")
        base = str(record.get("base_sha") or "")
        head = str(record.get("head_sha") or "")
        timestamp = _iso_date(record.get("timestamp"), f"records[{index}].timestamp", errors)
        paths = record.get("changed_paths")
        failed = record.get("failed_modules")
        actual = record.get("actual_modules_run")
        if not isinstance(pr, int) or isinstance(pr, bool) or pr < 1:
            malformed_records.append(index)
            continue
        if not re.fullmatch(r"[0-9a-f]{40,64}", base) or not re.fullmatch(r"[0-9a-f]{40,64}", head):
            malformed_records.append(index)
            continue
        if timestamp is None or not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
            malformed_records.append(index)
            continue
        if not isinstance(failed, list) or not all(isinstance(item, str) for item in failed):
            malformed_records.append(index)
            continue
        if not isinstance(actual, list) or sorted(actual) != sorted(expected_modules):
            malformed_records.append(index)
            continue
        if record.get("full_validation_run") is not True:
            malformed_records.append(index)
            continue
        if start and timestamp < start or end and timestamp > end:
            malformed_records.append(index)
            continue
        pull_requests.add(pr)
        modulo = int(graduation.get("deterministic_full_audit_modulo") or 10)
        if modulo < 2:
            errors.append("deterministic_full_audit_modulo must be >= 2")
            modulo = 10
        sampled = deterministic_full_audit(head, modulo)
        if sampled:
            audit_count += 1
        if record.get("deterministic_full_audit") is not sampled:
            malformed_records.append(index)
            continue
        plan = shadow.build_plan(
            scope_config,
            paths,
            base=base,
            head=head,
            change_class=str(record.get("change_class") or "unknown"),
        )
        recorded_skips = record.get("would_skip")
        if recorded_skips is not None and sorted(recorded_skips) != sorted(plan["would_skip"]):
            malformed_records.append(index)
            continue
        missed = sorted(set(failed) & set(plan["would_skip"]))
        false_negatives.extend({"pull_request": pr, "head_sha": head, "module": module} for module in missed)
        if plan["full_validation_fallback"] and plan["would_skip"]:
            errors.append(f"records[{index}] did not select full validation for a fail-closed candidate")

    if malformed_records:
        errors.append(f"{len(set(malformed_records))} shadow records are incomplete, stale, or malformed")
    minimum_prs = int(graduation.get("minimum_unique_pull_requests") or 30)
    if len(pull_requests) < minimum_prs:
        errors.append(f"cohort has {len(pull_requests)} unique pull requests; {minimum_prs} required")
    if len(false_negatives) > int(graduation.get("maximum_false_negatives") or 0):
        errors.append(f"cohort contains {len(false_negatives)} false-negative validator skips")
    if not records:
        errors.append("no exact-candidate shadow records were supplied")
    status = "READY_FOR_HUMAN_REVIEW" if not errors else "NOT_READY"
    return {
        "version": 1,
        "status": status,
        "observation_window_days": window_days,
        "unique_pull_request_count": len(pull_requests),
        "record_count": len(records),
        "deterministic_full_audit_count": audit_count,
        "false_negative_count": len(false_negatives),
        "false_negatives": false_negatives,
        "errors": errors,
        "selective_execution_enabled": False,
        "automatic_activation_authorized": False,
        "human_decision_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "config/validation-graduation.yaml")
    parser.add_argument("--scope-config", type=Path, default=ROOT / "config/validation-scope.yaml")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        config = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
        scope = yaml.safe_load(args.scope_config.read_text(encoding="utf-8")) or {}
        dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
        report = evaluate(config, scope, dataset)
    except (OSError, json.JSONDecodeError, yaml.YAMLError, GraduationError) as exc:
        report = {"version": 1, "status": "NOT_READY", "errors": [type(exc).__name__], "selective_execution_enabled": False, "automatic_activation_authorized": False, "human_decision_required": True}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "READY_FOR_HUMAN_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
