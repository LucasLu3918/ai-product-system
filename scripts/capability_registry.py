"""Validate and generate the compatible Capability Map and surface inventory."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


class RegistryError(ValueError):
    pass


def load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise RegistryError(f"{path}: expected a YAML mapping")
    return value


def confined(root: Path, raw: str) -> Path:
    path = (root / raw).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise RegistryError(f"registry path escapes repository: {raw}") from exc
    return path


def projections(registry: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    capabilities = registry.get("capabilities")
    surfaces = registry.get("surfaces")
    if not isinstance(capabilities, list) or not isinstance(surfaces, list):
        raise RegistryError("capabilities and surfaces must be lists")
    legacy_map = {
        "version": 1,
        "purpose": "Compact current-AIPS capability index for Evolution Radar semantic comparison; canonical behavior remains in referenced protocols.",
        "capabilities": [
            {
                "id": item["id"],
                "name_en": item["name_en"],
                "name_zh": item["name_zh"],
                "docs": item["docs"],
            }
            for item in capabilities
        ],
    }
    architecture = {
        "version": 1,
        "purpose": "Deterministic inventory of major AIPS architecture surfaces and their capability, repository, documentation, and validation bindings.",
        "policy": registry.get("surface_policy", {
            "capability_accounting": "complete",
            "validation_binding": "scenario_or_repository_validator",
        }),
        "surfaces": surfaces,
    }
    return legacy_map, architecture


def validate(root: Path, registry: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    capabilities = registry.get("capabilities")
    surfaces = registry.get("surfaces")
    if registry.get("version") != 1:
        issues.append("registry version must be 1")
    if not isinstance(capabilities, list) or not isinstance(surfaces, list):
        return [*issues, "capabilities and surfaces must be lists"]
    capability_ids: set[str] = set()
    for item in capabilities:
        if not isinstance(item, dict):
            issues.append("capability entry must be a mapping")
            continue
        capability_id = str(item.get("id") or "")
        if not capability_id or capability_id in capability_ids:
            issues.append(f"missing or duplicate capability id: {capability_id!r}")
        capability_ids.add(capability_id)
        for field in ("name_en", "name_zh", "surface_id", "maturity", "runtime_support"):
            if not item.get(field):
                issues.append(f"{capability_id}: missing {field}")
        if item.get("runtime_support") not in {"NOT_ASSESSED", "ADVISORY", "SUPPORTED"}:
            issues.append(f"{capability_id}: invalid runtime_support")
        for field in ("docs", "validation_evidence"):
            paths = item.get(field)
            if not isinstance(paths, list) or not paths:
                issues.append(f"{capability_id}: {field} must be a non-empty list")
                continue
            for raw in paths:
                try:
                    path = confined(root, str(raw))
                except RegistryError as exc:
                    issues.append(str(exc))
                    continue
                if not path.is_file():
                    issues.append(f"{capability_id}: {field} target missing: {raw}")

    surface_ids: set[str] = set()
    assignments: dict[str, str] = {}
    for surface in surfaces:
        if not isinstance(surface, dict):
            issues.append("surface entry must be a mapping")
            continue
        surface_id = str(surface.get("id") or "")
        if not surface_id or surface_id in surface_ids:
            issues.append(f"missing or duplicate surface id: {surface_id!r}")
        surface_ids.add(surface_id)
        members = surface.get("capabilities")
        if not isinstance(members, list) or not members:
            issues.append(f"{surface_id}: capabilities must be a non-empty list")
            members = []
        for capability_id in members:
            if capability_id not in capability_ids:
                issues.append(f"{surface_id}: unknown capability {capability_id}")
            if capability_id in assignments:
                issues.append(f"{capability_id}: assigned to multiple surfaces")
            assignments[capability_id] = surface_id
        for field in ("required_paths", "canonical_docs", "validation_paths"):
            paths = surface.get(field)
            if not isinstance(paths, list) or not paths:
                issues.append(f"{surface_id}: {field} must be a non-empty list")
                continue
            for raw in paths:
                try:
                    path = confined(root, str(raw))
                except RegistryError as exc:
                    issues.append(str(exc))
                    continue
                if not path.is_file():
                    issues.append(f"{surface_id}: {field} target missing: {raw}")
    for item in capabilities:
        if isinstance(item, dict):
            capability_id = str(item.get("id") or "")
            surface_id = str(item.get("surface_id") or "")
            if assignments.get(capability_id) != surface_id:
                issues.append(f"{capability_id}: surface_id does not match surface membership")
    if set(assignments) != capability_ids:
        issues.append("every capability must be assigned to exactly one surface")
    return sorted(set(issues))


def render(value: dict[str, Any]) -> str:
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=120)


def run(root: Path, command: str) -> int:
    registry_path = root / "config/capability-registry.yaml"
    registry = load(registry_path)
    issues = validate(root, registry)
    if issues:
        raise RegistryError("\n".join(issues))
    map_value, architecture_value = projections(registry)
    targets = (
        (root / "references/evolution/CAPABILITY_MAP.yaml", map_value),
        (root / "config/architecture-surfaces.yaml", architecture_value),
    )
    if command == "generate":
        for path, value in targets:
            path.write_text(render(value), encoding="utf-8")
        print("capability registry projections generated")
        return 0
    stale = [str(path.relative_to(root)) for path, value in targets if not path.exists() or path.read_text(encoding="utf-8") != render(value)]
    if stale:
        raise RegistryError("stale generated projections: " + ", ".join(stale))
    print(f"capability registry valid: {len(registry['capabilities'])} capabilities, {len(registry['surfaces'])} surfaces")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "validate", "generate"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        return run(args.root.resolve(), "generate" if args.command == "generate" else "check")
    except (OSError, RegistryError, yaml.YAMLError) as exc:
        print(f"CAPABILITY_REGISTRY_ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
