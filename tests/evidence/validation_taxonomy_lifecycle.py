"""Lifecycle checks for read-only validation taxonomy consistency audit."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import validation_taxonomy


def main() -> int:
    scope = {"full_validation_classes": ["large", "core"], "full_validation_path_prefixes": ["tests/", "scripts/validation_"]}
    graduation = {"graduation": {"full_validation_change_classes": ["core", "large"], "full_validation_path_prefixes": ["scripts/validation_", "tests/"]}}
    aligned = validation_taxonomy.evaluate(scope, graduation)
    assert aligned["status"] == "ALIGNED", aligned
    assert aligned["source_configs_modified"] is False
    assert aligned["selective_execution_enabled"] is False

    drift = copy.deepcopy(graduation)
    drift["graduation"]["full_validation_path_prefixes"].append("config/")
    report = validation_taxonomy.evaluate(scope, drift)
    assert report["status"] == "DRIFT", report
    assert report["comparisons"]["full_validation_path_prefixes"]["graduation_only"] == ["config/"]

    duplicate = copy.deepcopy(scope)
    duplicate["full_validation_classes"].append("core")
    assert validation_taxonomy.evaluate(duplicate, graduation)["status"] == "DRIFT"

    missing = copy.deepcopy(graduation)
    del missing["graduation"]["full_validation_change_classes"]
    assert validation_taxonomy.evaluate(scope, missing)["status"] == "INCOMPLETE"
    print("validation taxonomy lifecycle: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
