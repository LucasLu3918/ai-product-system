"""Check that validation shadow and graduation policies share one taxonomy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCOPE_CONFIG = ROOT / "config/validation-scope.yaml"
GRADUATION_CONFIG = ROOT / "config/validation-graduation.yaml"
FIELDS = {
    "full_validation_classes": ("full_validation_classes", "graduation.full_validation_change_classes"),
    "full_validation_path_prefixes": ("full_validation_path_prefixes", "graduation.full_validation_path_prefixes"),
}


def _values(document: dict[str, Any], path: str) -> list[str] | None:
    current: Any = document
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    if not isinstance(current, list) or not all(isinstance(item, str) and item for item in current):
        return None
    return current


def evaluate(scope: dict[str, Any], graduation: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    errors: list[str] = []
    for name, (scope_path, graduation_path) in FIELDS.items():
        left = _values(scope, scope_path)
        right = _values(graduation, graduation_path)
        if left is None or right is None:
            errors.append(f"{name} must be present as lists of non-empty strings in both policies")
            comparisons[name] = {"status": "INCOMPLETE"}
            continue
        duplicates = sorted(
            {item for values in (left, right) for item in values if values.count(item) > 1}
        )
        if len(left) != len(set(left)) or len(right) != len(set(right)):
            errors.append(f"{name} contains duplicate declarations")
        left_only = sorted(set(left) - set(right))
        right_only = sorted(set(right) - set(left))
        aligned = not left_only and not right_only and not duplicates
        if not aligned:
            errors.append(f"{name} diverges or contains duplicates")
        comparisons[name] = {
            "status": "ALIGNED" if aligned else "DRIFT",
            "scope_count": len(left),
            "graduation_count": len(right),
            "scope_only": left_only,
            "graduation_only": right_only,
            "duplicates": duplicates,
        }
    return {
        "version": 1,
        "status": "ALIGNED" if not errors else "DRIFT" if all(item.get("status") != "INCOMPLETE" for item in comparisons.values()) else "INCOMPLETE",
        "comparisons": comparisons,
        "errors": errors,
        "source_configs_modified": False,
        "selective_execution_enabled": False,
        "human_decision_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", type=Path, default=SCOPE_CONFIG)
    parser.add_argument("--graduation", type=Path, default=GRADUATION_CONFIG)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        scope = yaml.safe_load(args.scope.read_text(encoding="utf-8")) or {}
        graduation = yaml.safe_load(args.graduation.read_text(encoding="utf-8")) or {}
        if not isinstance(scope, dict) or not isinstance(graduation, dict):
            raise TypeError("both policy documents must be mappings")
        report = evaluate(scope, graduation)
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        report = {"version": 1, "status": "INCOMPLETE", "comparisons": {}, "errors": [type(exc).__name__], "source_configs_modified": False, "selective_execution_enabled": False, "human_decision_required": True}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "ALIGNED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
