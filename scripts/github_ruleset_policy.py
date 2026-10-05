#!/usr/bin/env python3
"""Compare supplied GitHub protection snapshots without API writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_CURRENT_FIELDS = ("branch_protection", "rulesets", "bypass_actors", "source_complete")


def assess(current: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REQUIRED_CURRENT_FIELDS if key not in current]
    if current.get("source_complete") is not True:
        missing.append("complete_admin_read")
    if missing:
        return {"status": "UNKNOWN", "missing_evidence": sorted(set(missing)), "diff": [],
                "activation_authorized": False, "required_checks_added": []}
    protection = current.get("branch_protection") or {}
    current_checks = set(protection.get("required_checks") or [])
    desired_checks = set(desired.get("required_status_checks") or [])
    added_checks = sorted(desired_checks - current_checks)
    diff = []
    current_rulesets = current.get("rulesets") or []
    if current_rulesets:
        diff.append({"area": "rulesets", "current_count": len(current_rulesets), "desired": "review before activation"})
    if "repository" not in current_checks and "repository" in desired_checks:
        diff.append({"area": "required_checks", "current": sorted(current_checks), "desired": sorted(desired_checks)})
    return {
        "status": "REVIEW_REQUIRED" if diff or added_checks else "NO_CHANGE",
        "missing_evidence": [], "diff": diff,
        "current_required_checks": sorted(current_checks),
        "desired_required_checks": sorted(desired_checks),
        "required_checks_added": added_checks,
        "activation_authorized": False, "api_write_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--policy", type=Path, default=ROOT / "config/github-ruleset-policy.yaml")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    current = yaml.safe_load(args.current.read_text(encoding="utf-8")) or {}
    policy = yaml.safe_load(args.policy.read_text(encoding="utf-8")) or {}
    report = assess(current, policy.get("policy") or {})
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] != "UNKNOWN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
