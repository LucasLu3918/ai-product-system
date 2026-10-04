#!/usr/bin/env python3
"""Build a fail-closed, exact-path plan for optional CI toolchains."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

import yaml


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class PlanError(ValueError):
    pass


def changed_paths(root: Path, base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "-z", "--diff-filter=ACDMRTUXB", base, head, "--"],
        cwd=root, capture_output=True, check=False,
    )
    if result.returncode:
        raise PlanError(f"cannot diff exact candidate {base}..{head}: {result.stderr.decode(errors='replace').strip()}")
    return sorted({part.decode("utf-8", errors="strict") for part in result.stdout.split(b"\0") if part})


def matches(path: str, selectors: list[str]) -> bool:
    return any(path == selector or path.startswith(selector) for selector in selectors)


def build_plan(config: dict[str, Any], paths: list[str], *, base: str, head: str) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise PlanError("CI validation plan config must be a mapping")
    if config.get("version") != 1:
        raise PlanError("CI validation plan config version must be 1")
    full_paths = set(config.get("full_validation_paths") or [])
    known_prefixes = tuple(config.get("known_path_prefixes") or [])
    known_roots = set(config.get("known_root_paths") or [])
    unknown = [path for path in paths if path not in known_roots and not path.startswith(known_prefixes)]
    force_full = bool(unknown or full_paths.intersection(paths))
    capability_paths = config.get("capabilities") or {}
    selected = {
        name: force_full or any(matches(path, selectors or []) for path in paths)
        for name, selectors in capability_paths.items()
    }
    return {
        "version": 1,
        "base": base,
        "head": head,
        "changed_paths": paths,
        "unknown_paths": unknown,
        "full_validation": force_full,
        "needs_node": selected.get("node", force_full),
        "needs_browser": selected.get("browser", force_full),
        "needs_openapi": selected.get("openapi", force_full),
        "reason": "unknown_path_fail_closed" if unknown else "sensitive_or_planner_path" if full_paths.intersection(paths) else "exact_path_plan",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    config_path = args.config or root / "config/ci-validation-plan.yaml"
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        plan = build_plan(config, changed_paths(root, args.base, args.head), base=args.base, head=args.head)
    except (OSError, UnicodeError, yaml.YAMLError, PlanError) as exc:
        print(json.dumps({"version": 1, "full_validation": True, "needs_node": True, "needs_browser": True, "needs_openapi": True, "reason": "planner_error_fail_closed", "error": str(exc)}, sort_keys=True))
        return 0
    rendered = json.dumps(plan, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
