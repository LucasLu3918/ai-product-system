#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"deterministic", "lifecycle", "agent_eval", "manual", "uncovered"}
AUTOMATED = {"deterministic", "lifecycle", "agent_eval"}
SCENARIO_RE = re.compile(r"^(\d{3})-.*\.md$")

def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("registry must be a mapping")
    return data

def scenario_inventory(directory: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(directory.glob("*.md")):
        m = SCENARIO_RE.match(path.name)
        if not m:
            continue
        result[m.group(1)] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    return result

def analyze(registry_path: Path, scenario_dir: Path) -> dict[str, Any]:
    doc = load_yaml(registry_path)
    entries = doc.get("scenarios") or []
    if not isinstance(entries, list):
        return {"status": "FAIL", "errors": ["registry.scenarios must be a list"], "coverage": {}}

    inventory = scenario_inventory(scenario_dir)
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    registered: dict[str, dict[str, Any]] = {}
    counts = {key: 0 for key in sorted(ALLOWED)}

    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("scenario registry entry must be a mapping")
            continue
        sid = str(entry.get("id") or "").zfill(3)
        path = str(entry.get("path") or "")
        coverage = str(entry.get("coverage") or "")
        evidence = entry.get("evidence") or []

        if sid in seen_ids:
            errors.append(f"duplicate scenario id: {sid}")
        seen_ids.add(sid)
        if path in seen_paths:
            errors.append(f"duplicate scenario path: {path}")
        seen_paths.add(path)
        registered[sid] = entry

        if coverage not in ALLOWED:
            errors.append(f"scenario {sid} has unknown coverage type: {coverage}")
        else:
            counts[coverage] += 1

        expected_path = inventory.get(sid)
        if expected_path is None:
            errors.append(f"registry references unknown scenario: {sid}")
        elif path != expected_path:
            errors.append(f"scenario {sid} path mismatch: registry={path} actual={expected_path}")

        if coverage != "uncovered" and not evidence:
            errors.append(f"scenario {sid} coverage {coverage} has no evidence")
        if not isinstance(evidence, list):
            errors.append(f"scenario {sid} evidence must be a list")
            evidence = []

        existing_evidence = 0
        non_scenario_evidence = 0
        for item in evidence:
            ref = str(item)
            if ref.startswith("external:"):
                existing_evidence += 1
                non_scenario_evidence += 1
                continue
            p = ROOT / ref
            if not p.exists():
                errors.append(f"scenario {sid} evidence missing: {ref}")
            else:
                existing_evidence += 1
                if ref != path:
                    non_scenario_evidence += 1
        if coverage in AUTOMATED and existing_evidence and non_scenario_evidence == 0:
            errors.append(f"scenario {sid} automated coverage cannot rely only on its scenario Markdown")

    missing = sorted(set(inventory) - set(registered))
    for sid in missing:
        errors.append(f"scenario missing registry entry: {sid}")

    policy = doc.get("policy") or {}
    if (policy.get("release_requires") or {}).get("no_uncovered") and counts.get("uncovered", 0):
        errors.append("registry policy forbids uncovered scenarios")

    total = len(inventory)
    automated = sum(counts.get(k, 0) for k in AUTOMATED)
    coverage = {
        "total": total,
        **counts,
        "automated": automated,
        "automated_percent": round((automated / total * 100.0) if total else 0.0, 1),
        "registered": len(entries),
        "missing": len(missing),
    }
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "coverage": coverage}

def emit(data: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())

def main() -> int:
    p = argparse.ArgumentParser(description="AIPS Scenario Conformance checker")
    p.add_argument("command", choices=["check", "report"])
    p.add_argument("--registry", default=str(ROOT / "tests" / "scenario_coverage.yaml"))
    p.add_argument("--scenario-dir", default=str(ROOT / "tests" / "scenarios"))
    p.add_argument("--format", choices=["yaml", "json"], default="yaml")
    args = p.parse_args()
    try:
        data = analyze(Path(args.registry).resolve(), Path(args.scenario_dir).resolve())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        data = {"status": "FAIL", "errors": [str(exc)], "coverage": {}}
    emit(data, args.format)
    return 0 if (args.command == "report" or data["status"] == "PASS") else 2

if __name__ == "__main__":
    raise SystemExit(main())
