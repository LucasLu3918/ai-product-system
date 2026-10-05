#!/usr/bin/env python3
"""Build a deterministic advisory validator selection plan; never skips execution."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from validation.registry import VALIDATORS  # noqa: E402


class ShadowPlanError(ValueError):
    pass


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def changed_paths(root: Path, base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "-z", "--diff-filter=ACDMRTUXB", base, head, "--"],
        cwd=root, capture_output=True, check=False,
    )
    if result.returncode:
        raise ShadowPlanError("cannot resolve exact candidate path set")
    try:
        return sorted({part.decode("utf-8", errors="strict") for part in result.stdout.split(b"\0") if part})
    except UnicodeDecodeError as exc:
        raise ShadowPlanError("candidate path list is not valid UTF-8") from exc


def build_plan(config: dict[str, Any], paths: list[str], *, base: str, head: str, change_class: str) -> dict[str, Any]:
    if not isinstance(config, dict) or config.get("version") != 1:
        raise ShadowPlanError("validation scope config must be version 1")
    if change_class not in {"standard", "large", "core", "release", "unknown"}:
        raise ShadowPlanError("change_class is invalid")
    known_prefixes = tuple(config.get("known_path_prefixes") or [])
    known_roots = set(config.get("known_root_paths") or [])
    unknown_paths = [path for path in paths if path not in known_roots and not path.startswith(known_prefixes)]
    full_path_prefixes = tuple(config.get("full_validation_path_prefixes") or [])
    force_full = bool(
        unknown_paths
        or change_class in set(config.get("full_validation_classes") or [])
        or set(paths).intersection(config.get("full_validation_paths") or [])
        or any(path.startswith(full_path_prefixes) for path in paths)
    )
    scoped: list[dict[str, Any]] = []
    for spec in VALIDATORS:
        matched = sorted(
            path for path in paths
            if any(fnmatch.fnmatchcase(path, pattern) for pattern in spec.paths)
        )
        run = force_full or spec.always_run or not spec.paths or bool(matched)
        if force_full:
            reason = "full_validation_fallback"
        elif spec.always_run:
            reason = "always_run"
        elif matched:
            reason = "declared_path_match"
        else:
            reason = "shadow_candidate_no_declared_path_match"
        scoped.append({
            "module": spec.module,
            "would_run": run,
            "actual_run": True,
            "parallel_safe": spec.parallel_safe,
            "matched_paths": matched,
            "reason": reason,
        })
    would_run = [item["module"] for item in scoped if item["would_run"]]
    would_skip = [item["module"] for item in scoped if not item["would_run"]]
    return {
        "version": 1,
        "mode": "FULL_RUN_SHADOW",
        "base": base,
        "head": head,
        "change_class": change_class,
        "changed_paths": sorted(set(paths)),
        "changed_paths_digest": _canonical_digest(sorted(set(paths))),
        "plan_fingerprint": _canonical_digest({"base": base, "head": head, "change_class": change_class, "paths": sorted(set(paths)), "validators": scoped}),
        "full_validation_fallback": force_full,
        "unknown_paths": unknown_paths,
        "would_run": would_run,
        "would_skip": would_skip,
        "actual_modules_run": [spec.module for spec in VALIDATORS],
        "replay_status": "NOT_RUN",
        "selective_execution_enabled": False,
        "validators": scoped,
        "authority": {"execution_skips_authorized": False, "human_review_required": True},
    }


def replay(config: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Replay recorded failure labels against advisory plans; never changes execution."""
    results = []
    false_negatives = []
    for index, record in enumerate(records):
        plan = build_plan(
            config,
            [str(path) for path in record.get("changed_paths") or []],
            base=str(record.get("base") or "recorded-base"),
            head=str(record.get("head") or f"recorded-head-{index}"),
            change_class=str(record.get("change_class") or "unknown"),
        )
        failed = sorted(set(str(module) for module in record.get("failed_modules") or []))
        missed = sorted(set(failed) & set(plan["would_skip"]))
        false_negatives.extend({"record": index, "module": module} for module in missed)
        results.append({"record": index, "failed_modules": failed, "would_skip": plan["would_skip"], "false_negatives": missed})
    return {
        "status": "PASS" if records and not false_negatives else "FAIL" if false_negatives else "NO_RECORDS",
        "record_count": len(records), "corpus_kind": "caller_supplied_recorded_runs",
        "results": results, "false_negatives": false_negatives,
        "selective_execution_enabled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--change-class", choices=("standard", "large", "core", "release", "unknown"), default="unknown")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay-json", type=Path, help="JSON list of historical runs with changed_paths/change_class/failed_modules")
    args = parser.parse_args()
    root = args.root.resolve()
    config_path = args.config or root / "config/validation-scope.yaml"
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        plan = build_plan(config, changed_paths(root, args.base, args.head), base=args.base, head=args.head, change_class=args.change_class)
        if args.replay_json:
            records = json.loads(args.replay_json.read_text(encoding="utf-8"))
            if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
                raise ShadowPlanError("replay input must be a list of recorded-run mappings")
            plan["replay"] = replay(config, records)
            plan["replay_status"] = plan["replay"]["status"]
    except (OSError, UnicodeError, yaml.YAMLError, ShadowPlanError) as exc:
        plan = {
            "version": 1,
            "mode": "FULL_RUN_SHADOW",
            "base": args.base,
            "head": args.head,
            "change_class": args.change_class,
            "full_validation_fallback": True,
            "reason": "planner_error_fail_closed",
            "error_category": type(exc).__name__,
            "would_run": [spec.module for spec in VALIDATORS],
            "would_skip": [],
            "actual_modules_run": [spec.module for spec in VALIDATORS],
            "replay_status": "NOT_RUN",
            "selective_execution_enabled": False,
            "authority": {"execution_skips_authorized": False, "human_review_required": True},
        }
    rendered = json.dumps(plan, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
