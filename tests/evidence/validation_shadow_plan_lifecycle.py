#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import validation_shadow_plan as shadow  # noqa: E402


def main() -> int:
    config = yaml.safe_load((ROOT / "config/validation-scope.yaml").read_text(encoding="utf-8")) or {}
    paths = ["scripts/evolution_radar.py", "tests/evidence/evolution_radar_lifecycle.py"]
    first = shadow.build_plan(config, paths, base="a" * 40, head="b" * 40, change_class="standard")
    second = shadow.build_plan(config, paths, base="a" * 40, head="b" * 40, change_class="standard")
    assert first == second, "same exact candidate must produce an identical shadow plan"
    assert first["mode"] == "FULL_RUN_SHADOW" and first["replay_status"] == "NOT_RUN"
    assert first["selective_execution_enabled"] is False
    assert first["authority"]["execution_skips_authorized"] is False
    assert first["actual_modules_run"] == [item.module for item in shadow.VALIDATORS]
    assert all(item["actual_run"] for item in first["validators"]), "shadow selection must preserve the complete executed set"
    assert "validation.evolution_radar_contracts" in first["would_run"]
    assert first["would_skip"], "scoped validators should be measurable as advisory shadow skips"

    unknown = shadow.build_plan(config, ["unregistered/new-boundary/file.py"], base="a" * 40, head="c" * 40, change_class="standard")
    assert unknown["full_validation_fallback"] is True
    assert unknown["would_skip"] == []

    for change_class in ("large", "core", "release", "unknown"):
        full = shadow.build_plan(config, paths, base="a" * 40, head="d" * 40, change_class=change_class)
        assert full["full_validation_fallback"] is True
        assert full["would_skip"] == []
        assert full["actual_modules_run"] == [item.module for item in shadow.VALIDATORS]

    replay = shadow.replay(config, [{
        "changed_paths": paths, "change_class": "standard",
        "failed_modules": ["validation.evolution_radar_contracts"],
    }])
    assert replay["status"] == "PASS" and replay["false_negatives"] == []
    assert replay["corpus_kind"] == "caller_supplied_recorded_runs"
    caught = shadow.replay(config, [{
        "changed_paths": paths, "change_class": "standard",
        "failed_modules": ["validation.product_delivery_contracts"],
    }])
    assert caught["status"] == "FAIL" and caught["false_negatives"], "replay must disclose a proposed false skip"
    assert caught["selective_execution_enabled"] is False

    print("VALIDATION SHADOW PLAN LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
