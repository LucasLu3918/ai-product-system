"""Select affected Agent Eval cases from changed behavior dependencies."""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from agent_eval import fingerprint, system_fingerprint


class FreshnessError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise FreshnessError(f"{path}: expected a mapping")
    return value


def changed_paths(root: Path, base: str) -> list[str]:
    exists = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", base + "^{commit}"],
        capture_output=True, text=True, check=False,
    )
    if exists.returncode:
        raise FreshnessError(f"base ref is unavailable: {base}")
    paths: set[str] = set()
    commands = (
        ["git", "-C", str(root), "diff", "--name-only", base + "...HEAD"],
        ["git", "-C", str(root), "diff", "--name-only", "HEAD"],
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
    )
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode:
            raise FreshnessError(result.stderr.strip() or "git could not enumerate changed files")
        paths.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    return sorted(paths)


def validate_config(root: Path, config: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if config.get("version") != 1:
        issues.append("config version must be 1")
    behaviors = config.get("behaviors")
    if not isinstance(behaviors, list) or not behaviors:
        return [*issues, "behaviors must be a non-empty list"]
    case_ids: set[str] = set()
    behavior_ids: set[str] = set()
    for behavior in behaviors:
        if not isinstance(behavior, dict):
            issues.append("behavior entry must be a mapping")
            continue
        behavior_id = str(behavior.get("id") or "")
        if not behavior_id or behavior_id in behavior_ids:
            issues.append(f"missing or duplicate behavior id: {behavior_id!r}")
        behavior_ids.add(behavior_id)
        patterns = behavior.get("path_patterns")
        cases = behavior.get("case_ids")
        if not isinstance(patterns, list) or not patterns:
            issues.append(f"{behavior_id}: path_patterns must be non-empty")
        if not isinstance(cases, list) or not cases:
            issues.append(f"{behavior_id}: case_ids must be non-empty")
        for pattern in patterns or []:
            rel = PurePosixPath(str(pattern))
            if rel.is_absolute() or ".." in rel.parts:
                issues.append(f"{behavior_id}: unsafe dependency pattern: {pattern}")
        for case_id in cases or []:
            if case_id in case_ids:
                # Reusing a case across behaviors is expected; only validate file existence once.
                continue
            case_ids.add(case_id)
            case_path = root / str(config.get("case_dir") or "tests/agent_eval/cases") / f"{case_id}.yaml"
            if not case_path.is_file():
                issues.append(f"{behavior_id}: Agent Eval case is missing: {case_id}")
    authority = config.get("authority") or {}
    if authority.get("automatic_case_execution") is not False or authority.get("automatic_case_or_result_mutation") is not False:
        issues.append("automatic Agent Eval execution and mutation must remain disabled")
    return sorted(set(issues))


def build_report(root: Path, config: dict[str, Any], changed: list[str]) -> dict[str, Any]:
    issues = validate_config(root, config)
    if issues:
        raise FreshnessError("; ".join(issues))
    impacted: dict[str, set[str]] = {}
    for behavior in config["behaviors"]:
        patterns = [str(item) for item in behavior["path_patterns"]]
        matched = sorted(path for path in changed if any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns))
        if matched:
            for case_id in behavior["case_ids"]:
                impacted.setdefault(str(case_id), set()).add(str(behavior["id"]))

    case_dir = root / str(config.get("case_dir") or "tests/agent_eval/cases")
    result_dir = root / str(config.get("result_dir") or "tests/agent_eval/results")
    cases: list[dict[str, Any]] = []
    for case_id, behavior_ids in sorted(impacted.items()):
        case_path = case_dir / f"{case_id}.yaml"
        case = load_yaml(case_path)
        reasons = ["behavior_dependency_changed"]
        result_path = result_dir / f"{case_id}.yaml"
        if not result_path.is_file():
            reasons.append("result_missing")
        else:
            result = load_yaml(result_path)
            if result.get("case_fingerprint") != fingerprint(case):
                reasons.append("case_fingerprint_stale")
            recorded_system_fingerprint = (result.get("execution") or {}).get("system_fingerprint")
            expected_system_fingerprint = system_fingerprint(case)
            if recorded_system_fingerprint != expected_system_fingerprint:
                reasons.append("system_dependency_fingerprint_stale")
        cases.append({
            "case_id": case_id,
            "scenario_id": str(case.get("scenario_id") or ""),
            "behaviors": sorted(behavior_ids),
            "stale_reasons": sorted(set(reasons)),
        })
    manual = sorted(str(item) for item in config.get("manual_scenarios") or [])
    if any(row["scenario_id"] in manual for row in cases):
        raise FreshnessError("manual scenarios 192, 193 and 224 cannot be auto-selected as Agent Eval cases")
    return {
        "version": 1,
        "status": "STALE" if cases else "CURRENT",
        "changed_files": sorted(set(changed)),
        "affected_cases": cases,
        "manual_scenarios_preserved": manual,
        "authority": {
            "automatic_case_execution": False,
            "automatic_case_or_result_mutation": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report",))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--config", type=Path)
    parser.add_argument("--base")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--format", choices=("json", "yaml"), default="json")
    args = parser.parse_args()
    root = args.root.resolve()
    config_path = args.config or root / "config/eval-freshness.yaml"
    try:
        config = load_yaml(config_path)
        changed = args.changed_file or changed_paths(root, args.base or str(config.get("base_ref") or "origin/main"))
        report = build_report(root, config, changed)
        print(json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
        return 0
    except (OSError, FreshnessError, yaml.YAMLError) as exc:
        print(f"AGENT_EVAL_FRESHNESS_ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
