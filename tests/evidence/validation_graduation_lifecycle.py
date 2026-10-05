#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import validation_graduation as graduation
import validation_shadow_plan as shadow


def main() -> int:
    config = yaml.safe_load((ROOT / "config/validation-graduation.yaml").read_text())
    scope = yaml.safe_load((ROOT / "config/validation-scope.yaml").read_text())
    today = date(2026, 10, 5)
    modules = [spec.module for spec in shadow.VALIDATORS]
    records = []
    for index in range(30):
        head = f"{index + 1:040x}"
        paths = ["scripts/evolution_radar.py"]
        plan = shadow.build_plan(scope, paths, base="a" * 40, head=head, change_class="standard")
        records.append({
            "pull_request": index + 1,
            "base_sha": "a" * 40,
            "head_sha": head,
            "timestamp": (today - timedelta(days=29 - index)).isoformat(),
            "change_class": "standard",
            "changed_paths": paths,
            "failed_modules": [],
            "actual_modules_run": modules,
            "full_validation_run": True,
            "deterministic_full_audit": graduation.deterministic_full_audit(head, 10),
            "would_skip": plan["would_skip"],
        })
    dataset = {
        "window_start": (today - timedelta(days=29)).isoformat(),
        "window_end": today.isoformat(),
        "artifact_history_complete": True,
        "records": records,
    }
    ready = graduation.evaluate(config, scope, dataset)
    assert ready["status"] == "READY_FOR_HUMAN_REVIEW", ready
    assert ready["false_negative_count"] == 0
    assert ready["selective_execution_enabled"] is False
    assert ready["automatic_activation_authorized"] is False
    assert ready["deterministic_full_audit_count"] > 0

    partial = dict(dataset, artifact_history_complete=False)
    blocked = graduation.evaluate(config, scope, partial)
    assert blocked["status"] == "NOT_READY"
    assert any("incomplete" in error for error in blocked["errors"])

    missed_records = [dict(item) for item in records]
    skipped = next(iter(missed_records[0]["would_skip"]))
    missed_records[0]["failed_modules"] = [skipped]
    missed = graduation.evaluate(config, scope, dict(dataset, records=missed_records))
    assert missed["status"] == "NOT_READY" and missed["false_negative_count"] == 1

    validator_change = shadow.build_plan(
        scope, ["tests/validation/new_validator.py"], base="a" * 40,
        head="b" * 40, change_class="standard",
    )
    assert validator_change["full_validation_fallback"] is True
    assert validator_change["would_skip"] == []

    print("VALIDATION GRADUATION LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
