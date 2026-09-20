#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[1]
DRIFT_KEYS = (
    "missing_capability_targets",
    "orphan_capability_surfaces",
    "stale_documentation_links",
    "scenario_evidence_drift",
    "workflow_contract_drift",
)

def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    return data

def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def resolve(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {value}") from exc
    return path

def repository_revision(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "UNKNOWN"

def as_list(value: Any, name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value

def as_mapping(value: Any, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return value

def run_scenario_conformance(root: Path, helper: Path, registry: Path, scenario_dir: Path) -> list[str]:
    if not helper.exists():
        return [f"scenario helper missing: {helper.relative_to(root)}"]
    result = subprocess.run(
        [sys.executable, str(helper), "check", "--registry", str(registry),
         "--scenario-dir", str(scenario_dir), "--format", "json"],
        cwd=root, capture_output=True, text=True,
    )
    try:
        payload = json.loads(result.stdout)
        problems = payload.get("errors") or []
        if result.returncode == 0 and payload.get("status") == "PASS":
            return []
        if problems:
            return [str(item) for item in problems]
    except json.JSONDecodeError:
        pass
    detail = (result.stdout + "\n" + result.stderr).strip()
    return [f"scenario conformance failed: {detail[:1200]}"]

def analyze(root: Path, config_path: Path) -> dict[str, Any]:
    root = root.resolve()
    config_path = config_path.resolve()
    config = load_yaml(config_path)
    if config.get("version") != 1:
        raise ValueError("repository health config version must be 1")

    truth = as_mapping(config.get("truth_sources"), "truth_sources")
    capability_map_path = resolve(root, str(truth.get("capability_map") or "references/evolution/CAPABILITY_MAP.yaml"))
    scenario_registry_path = resolve(root, str(truth.get("scenario_registry") or "tests/scenario_coverage.yaml"))
    scenario_dir = resolve(root, str(truth.get("scenario_dir") or "tests/scenarios"))
    scenario_helper = resolve(root, str(truth.get("scenario_helper") or "scripts/scenario_conformance.py"))
    for required in (capability_map_path, scenario_registry_path):
        if not required.exists():
            raise ValueError(f"truth source missing: {required.relative_to(root)}")

    drift: dict[str, list[str]] = {key: [] for key in DRIFT_KEYS}
    capability_map = load_yaml(capability_map_path)
    capabilities = as_list(capability_map.get("capabilities"), "capability_map.capabilities")
    capability_ids: set[str] = set()
    for item in capabilities:
        if not isinstance(item, dict):
            drift["missing_capability_targets"].append("capability entry must be a mapping")
            continue
        capability_id = str(item.get("id") or "").strip()
        if not capability_id:
            drift["missing_capability_targets"].append("capability entry missing id")
            continue
        if capability_id in capability_ids:
            drift["missing_capability_targets"].append(f"duplicate capability id: {capability_id}")
        capability_ids.add(capability_id)
        docs = as_list(item.get("docs"), f"capability {capability_id}.docs")
        if not docs:
            drift["missing_capability_targets"].append(f"capability {capability_id} has no canonical docs")
        for raw in docs:
            rel = str(raw)
            if not resolve(root, rel).exists():
                drift["missing_capability_targets"].append(f"capability {capability_id} target missing: {rel}")

    surfaces = as_mapping(config.get("capability_surfaces"), "capability_surfaces")
    declared_surface_paths: set[str] = set()
    for capability_id, raw_surface in sorted(surfaces.items()):
        surface = as_mapping(raw_surface, f"capability_surfaces.{capability_id}")
        if capability_id not in capability_ids:
            drift["orphan_capability_surfaces"].append(
                f"configured core surface has no Capability Map entry: {capability_id}"
            )
        required_paths = as_list(surface.get("required"), f"capability_surfaces.{capability_id}.required")
        if not required_paths:
            drift["orphan_capability_surfaces"].append(f"configured core surface has no required paths: {capability_id}")
        for raw in required_paths:
            rel = str(raw)
            declared_surface_paths.add(rel)
            if not resolve(root, rel).exists():
                drift["orphan_capability_surfaces"].append(f"{capability_id} required surface missing: {rel}")

    discovery = as_mapping(config.get("surface_discovery"), "surface_discovery")
    patterns = [str(item) for item in as_list(discovery.get("patterns"), "surface_discovery.patterns")]
    ignored = {str(item) for item in as_list(discovery.get("ignore"), "surface_discovery.ignore")}
    discovered: set[str] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                discovered.add(path.relative_to(root).as_posix())
    for rel in sorted(discovered):
        if rel not in declared_surface_paths and rel not in ignored:
            drift["orphan_capability_surfaces"].append(f"unregistered discovered core surface: {rel}")

    for index, raw_binding in enumerate(as_list(config.get("documentation_bindings"), "documentation_bindings")):
        binding = as_mapping(raw_binding, f"documentation_bindings[{index}]")
        source_rel = str(binding.get("source") or "")
        if not source_rel:
            drift["stale_documentation_links"].append(f"documentation binding {index} missing source")
            continue
        source = resolve(root, source_rel)
        if not source.exists():
            drift["stale_documentation_links"].append(f"documentation source missing: {source_rel}")
            continue
        source_text = source.read_text(encoding="utf-8")
        for raw_ref in as_list(binding.get("required_references"),
                               f"documentation_bindings[{index}].required_references"):
            rel = str(raw_ref)
            if not resolve(root, rel).exists():
                drift["stale_documentation_links"].append(f"{source_rel} references missing target: {rel}")
            elif rel not in source_text:
                drift["stale_documentation_links"].append(f"{source_rel} missing canonical reference: {rel}")

    drift["scenario_evidence_drift"].extend(
        run_scenario_conformance(root, scenario_helper, scenario_registry_path, scenario_dir)
    )

    for index, raw_contract in enumerate(as_list(config.get("contract_files"), "contract_files")):
        contract = as_mapping(raw_contract, f"contract_files[{index}]")
        rel = str(contract.get("path") or "")
        if not rel:
            drift["workflow_contract_drift"].append(f"contract_files[{index}] missing path")
            continue
        path = resolve(root, rel)
        if not path.exists():
            drift["workflow_contract_drift"].append(f"contract file missing: {rel}")
            continue
        contract_text = path.read_text(encoding="utf-8")
        for raw_required in as_list(contract.get("required_strings"),
                                    f"contract_files[{index}].required_strings"):
            required = str(raw_required)
            if required not in contract_text:
                drift["workflow_contract_drift"].append(f"{rel} missing contract string: {required}")

    for key in DRIFT_KEYS:
        drift[key] = sorted(set(drift[key]))
    status = "PASS" if not any(drift.values()) else "DRIFT_DETECTED"
    return {
        "version": 1,
        "status": status,
        "repository_revision": repository_revision(root),
        "inputs": {
            "config": {"path": config_path.relative_to(root).as_posix(), "digest": file_digest(config_path)},
            "capability_map": {"path": capability_map_path.relative_to(root).as_posix(), "digest": file_digest(capability_map_path)},
            "scenario_registry": {"path": scenario_registry_path.relative_to(root).as_posix(), "digest": file_digest(scenario_registry_path)},
        },
        "drift": drift,
        "execution": {
            "deterministic": True,
            "credential_required": False,
            "external_network_required": False,
            "automatic_remediation_performed": False,
        },
        "authority": {
            "automatic_remediation_authorized": False,
            "code_change_authorized": False,
            "branch_or_pr_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "publication_authorized": False,
        },
    }

def emit(data: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())

def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic AIPS repository health / architecture drift detector")
    parser.add_argument("command", choices=["audit"])
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--config", default="config/repository-health.yaml")
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    config = Path(args.config)
    if not config.is_absolute():
        config = root / config
    try:
        data = analyze(root, config)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        data = {
            "version": 1, "status": "DRIFT_DETECTED",
            "repository_revision": repository_revision(root),
            "drift": {
                "missing_capability_targets": [], "orphan_capability_surfaces": [],
                "stale_documentation_links": [], "scenario_evidence_drift": [],
                "workflow_contract_drift": [str(exc)],
            },
            "execution": {
                "deterministic": True, "credential_required": False,
                "external_network_required": False, "automatic_remediation_performed": False,
            },
            "authority": {
                "automatic_remediation_authorized": False, "code_change_authorized": False,
                "branch_or_pr_authorized": False, "merge_authorized": False,
                "release_authorized": False, "publication_authorized": False,
            },
        }
    emit(data, args.format)
    return 0 if data.get("status") == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
