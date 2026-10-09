#!/usr/bin/env python3
"""Build a fail-closed, exact-path plan for optional CI toolchains."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml
from validation_path_classification import unknown_paths

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class PlanError(ValueError):
    pass


EVIDENCE_CAPABILITIES = {
    "implementation_enforcement_lifecycle.py": "openapi",
    "openapi_contracts_lifecycle.py": "openapi",
    "openapi_generator_adapter_lifecycle.py": "openapi",
    "openapi_client_pilot_lifecycle.py": "openapi",
    "openapi_cli_install_lifecycle.py": "openapi",
}


def validation_capabilities(plan: Any) -> dict[str, bool]:
    """Missing or malformed plans select every capability, never implicit skips."""
    names = ("node", "browser", "openapi")
    valid = (isinstance(plan, dict) and plan.get("version") == 1
             and all(type(plan.get(f"needs_{name}")) is bool for name in names))
    return {name: plan[f"needs_{name}"] if valid else True for name in names}


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


def build_plan(config: dict[str, Any], paths: list[str], *, base: str, head: str, path_inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise PlanError("CI validation plan config must be a mapping")
    if config.get("version") != 1:
        raise PlanError("CI validation plan config version must be 1")
    full_paths = set(config.get("full_validation_paths") or [])
    if path_inventory is None:
        inventory_path = DEFAULT_ROOT / "config/validation-path-inventory.yaml"
        path_inventory = yaml.safe_load(inventory_path.read_text(encoding="utf-8")) or {}
    unknown = unknown_paths(paths, path_inventory)
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
        inventory = yaml.safe_load((root / "config/validation-path-inventory.yaml").read_text(encoding="utf-8")) or {}
        plan = build_plan(config, changed_paths(root, args.base, args.head), base=args.base, head=args.head, path_inventory=inventory)
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
