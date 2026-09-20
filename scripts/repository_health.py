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
    "architecture_surface_drift",
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


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {value}") from exc
    return path


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def git_output(root: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def repository_state(root: Path) -> dict[str, Any]:
    head = git_output(root, ["rev-parse", "HEAD"])
    if head is None:
        return {
            "git_available": False,
            "head": "UNKNOWN",
            "dirty": False,
            "dirty_paths": [],
        }

    dirty: set[str] = set()
    for args in (
        ["diff", "--name-only"],
        ["diff", "--cached", "--name-only"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        raw = git_output(root, args)
        if raw:
            dirty.update(line for line in raw.splitlines() if line)

    return {
        "git_available": True,
        "head": head,
        "dirty": bool(dirty),
        "dirty_paths": sorted(dirty),
    }


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


def run_scenario_conformance(
    root: Path,
    helper: Path,
    registry: Path,
    scenario_dir: Path,
) -> list[str]:
    if not helper.exists():
        return [f"scenario helper missing: {relative_path(root, helper)}"]
    result = subprocess.run(
        [
            sys.executable,
            str(helper),
            "check",
            "--registry",
            str(registry),
            "--scenario-dir",
            str(scenario_dir),
            "--format",
            "json",
        ],
        cwd=root,
        capture_output=True,
        text=True,
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


def add_manifest_path(
    store: dict[str, set[str]],
    root: Path,
    raw_path: str | Path,
    role: str,
) -> None:
    path = raw_path if isinstance(raw_path, Path) else resolve(root, str(raw_path))
    rel = relative_path(root, path)
    store.setdefault(rel, set()).add(role)


def build_input_manifest(
    root: Path,
    config_path: Path,
    config: dict[str, Any],
    capability_map_path: Path,
    capability_map: dict[str, Any],
    architecture_inventory_path: Path,
    architecture_inventory: dict[str, Any],
    scenario_registry_path: Path,
    scenario_dir: Path,
    scenario_helper: Path,
    discovered_surfaces: set[str],
) -> dict[str, Any]:
    paths: dict[str, set[str]] = {}
    add_manifest_path(paths, root, config_path, "repository_health_config")
    add_manifest_path(paths, root, capability_map_path, "capability_map")
    add_manifest_path(
        paths,
        root,
        architecture_inventory_path,
        "architecture_surface_inventory",
    )
    add_manifest_path(paths, root, scenario_registry_path, "scenario_registry")
    add_manifest_path(paths, root, scenario_helper, "scenario_checker")

    for item in as_list(capability_map.get("capabilities"), "capability_map.capabilities"):
        if not isinstance(item, dict):
            continue
        for raw in as_list(item.get("docs"), "capability.docs"):
            add_manifest_path(paths, root, str(raw), "capability_target")

    for index, raw_surface in enumerate(
        as_list(architecture_inventory.get("surfaces"), "architecture_inventory.surfaces")
    ):
        surface = as_mapping(
            raw_surface,
            f"architecture_inventory.surfaces[{index}]",
        )
        for field, role in (
            ("required_paths", "architecture_surface"),
            ("canonical_docs", "architecture_canonical_doc"),
            ("validation_paths", "architecture_validation"),
        ):
            for raw in as_list(
                surface.get(field),
                f"architecture_inventory.surfaces[{index}].{field}",
            ):
                add_manifest_path(paths, root, str(raw), role)

    for rel in discovered_surfaces:
        add_manifest_path(paths, root, rel, "discovered_surface")

    for index, raw_binding in enumerate(
        as_list(config.get("documentation_bindings"), "documentation_bindings")
    ):
        binding = as_mapping(raw_binding, f"documentation_bindings[{index}]")
        source = str(binding.get("source") or "")
        if source:
            add_manifest_path(paths, root, source, "documentation_source")
        for raw in as_list(
            binding.get("required_references"),
            f"documentation_bindings[{index}].required_references",
        ):
            add_manifest_path(paths, root, str(raw), "documentation_target")

    for path in sorted(scenario_dir.glob("[0-9][0-9][0-9]-*.md")):
        add_manifest_path(paths, root, path, "scenario_inventory")

    scenario_registry = load_yaml(scenario_registry_path)
    for index, raw_entry in enumerate(
        as_list(scenario_registry.get("scenarios"), "scenario_registry.scenarios")
    ):
        entry = as_mapping(raw_entry, f"scenario_registry.scenarios[{index}]")
        scenario_path = str(entry.get("path") or "")
        if scenario_path:
            add_manifest_path(paths, root, scenario_path, "scenario_spec")
        for raw in as_list(
            entry.get("evidence"),
            f"scenario_registry.scenarios[{index}].evidence",
        ):
            ref = str(raw)
            if ref and not ref.startswith("external:"):
                add_manifest_path(paths, root, ref, "scenario_evidence")

    for index, raw_contract in enumerate(
        as_list(config.get("contract_files"), "contract_files")
    ):
        contract = as_mapping(raw_contract, f"contract_files[{index}]")
        rel = str(contract.get("path") or "")
        if rel:
            add_manifest_path(paths, root, rel, "contract_file")

    entries: list[dict[str, Any]] = []
    for rel in sorted(paths):
        path = resolve(root, rel)
        exists = path.is_file()
        entries.append(
            {
                "path": rel,
                "roles": sorted(paths[rel]),
                "exists": exists,
                "digest": file_digest(path) if exists else None,
            }
        )

    return {
        "count": len(entries),
        "digest": canonical_hash(entries),
        "entries": entries,
    }


def binding_status(workspace: dict[str, Any]) -> str:
    if not workspace.get("git_available"):
        return "NO_GIT"
    if workspace.get("dirty"):
        return "DIRTY_WORKTREE"
    return "EXACT_REVISION"


def analyze(root: Path, config_path: Path) -> dict[str, Any]:
    root = root.resolve()
    config_path = config_path.resolve()
    config = load_yaml(config_path)
    if config.get("version") != 1:
        raise ValueError("repository health config version must be 1")

    binding_policy = as_mapping(config.get("evidence_binding"), "evidence_binding")
    if binding_policy.get("manifest") != "complete":
        raise ValueError("evidence_binding.manifest must be complete")
    if binding_policy.get("dirty_workspace") != "report_non_reproducible":
        raise ValueError(
            "evidence_binding.dirty_workspace must be report_non_reproducible"
        )

    truth = as_mapping(config.get("truth_sources"), "truth_sources")
    capability_map_path = resolve(
        root,
        str(
            truth.get("capability_map")
            or "references/evolution/CAPABILITY_MAP.yaml"
        ),
    )
    scenario_registry_path = resolve(
        root,
        str(truth.get("scenario_registry") or "tests/scenario_coverage.yaml"),
    )
    scenario_dir = resolve(
        root,
        str(truth.get("scenario_dir") or "tests/scenarios"),
    )
    scenario_helper = resolve(
        root,
        str(truth.get("scenario_helper") or "scripts/scenario_conformance.py"),
    )
    architecture_inventory_path = resolve(
        root,
        str(
            truth.get("architecture_surfaces")
            or "config/architecture-surfaces.yaml"
        ),
    )
    repository_validator_path = resolve(
        root,
        str(
            truth.get("repository_validator")
            or "tests/validate_repository.py"
        ),
    )
    for required in (capability_map_path, scenario_registry_path):
        if not required.exists():
            raise ValueError(
                f"truth source missing: {relative_path(root, required)}"
            )

    drift: dict[str, list[str]] = {key: [] for key in DRIFT_KEYS}
    capability_map = load_yaml(capability_map_path)
    capabilities = as_list(
        capability_map.get("capabilities"),
        "capability_map.capabilities",
    )
    capability_ids: set[str] = set()
    capability_docs_by_id: dict[str, set[str]] = {}

    for item in capabilities:
        if not isinstance(item, dict):
            drift["missing_capability_targets"].append(
                "capability entry must be a mapping"
            )
            continue
        capability_id = str(item.get("id") or "").strip()
        if not capability_id:
            drift["missing_capability_targets"].append(
                "capability entry missing id"
            )
            continue
        if capability_id in capability_ids:
            drift["missing_capability_targets"].append(
                f"duplicate capability id: {capability_id}"
            )
        capability_ids.add(capability_id)
        docs = as_list(item.get("docs"), f"capability {capability_id}.docs")
        capability_docs_by_id.setdefault(capability_id, set()).update(
            str(raw) for raw in docs
        )
        if not docs:
            drift["missing_capability_targets"].append(
                f"capability {capability_id} has no canonical docs"
            )
        for raw in docs:
            rel = str(raw)
            if not resolve(root, rel).exists():
                drift["missing_capability_targets"].append(
                    f"capability {capability_id} target missing: {rel}"
                )

    scenario_registry = load_yaml(scenario_registry_path)
    scenario_evidence_paths: set[str] = set()
    for index, raw_entry in enumerate(
        as_list(scenario_registry.get("scenarios"), "scenario_registry.scenarios")
    ):
        entry = as_mapping(
            raw_entry,
            f"scenario_registry.scenarios[{index}]",
        )
        for raw in as_list(
            entry.get("evidence"),
            f"scenario_registry.scenarios[{index}].evidence",
        ):
            rel = str(raw)
            if rel and not rel.startswith("external:"):
                scenario_evidence_paths.add(rel)

    repository_validator_text = (
        repository_validator_path.read_text(encoding="utf-8")
        if repository_validator_path.exists()
        else ""
    )

    def validation_path_is_bound(rel: str) -> bool:
        if rel in scenario_evidence_paths:
            return True
        if rel.startswith("tests/validation/") and rel.endswith(".py"):
            module = Path(rel).stem
            return f"from validation import {module}" in repository_validator_text
        return False

    architecture_inventory: dict[str, Any] = {}
    if architecture_inventory_path.exists():
        architecture_inventory = load_yaml(architecture_inventory_path)
    else:
        drift["architecture_surface_drift"].append(
            "architecture surface inventory missing: "
            f"{relative_path(root, architecture_inventory_path)}"
        )

    if architecture_inventory.get("version") != 1:
        drift["architecture_surface_drift"].append(
            "architecture surface inventory version must be 1"
        )

    inventory_policy = as_mapping(
        architecture_inventory.get("policy"),
        "architecture_inventory.policy",
    )
    if inventory_policy.get("capability_accounting") != "complete":
        drift["architecture_surface_drift"].append(
            "architecture surface inventory capability_accounting "
            "must be complete"
        )
    if (
        inventory_policy.get("validation_binding")
        != "scenario_or_repository_validator"
    ):
        drift["architecture_surface_drift"].append(
            "architecture surface inventory validation_binding must be "
            "scenario_or_repository_validator"
        )

    declared_surface_paths: set[str] = set()
    assigned_capabilities: dict[str, str] = {}
    surface_ids: set[str] = set()
    validation_paths_seen: set[str] = set()
    raw_surfaces = as_list(
        architecture_inventory.get("surfaces"),
        "architecture_inventory.surfaces",
    )
    if not raw_surfaces:
        drift["architecture_surface_drift"].append(
            "architecture surface inventory must declare surfaces"
        )

    for index, raw_surface in enumerate(raw_surfaces):
        surface = as_mapping(
            raw_surface,
            f"architecture_inventory.surfaces[{index}]",
        )
        surface_id = str(surface.get("id") or "").strip()
        if not surface_id:
            drift["architecture_surface_drift"].append(
                f"architecture surface {index} missing id"
            )
            surface_id = f"<index:{index}>"
        elif surface_id in surface_ids:
            drift["architecture_surface_drift"].append(
                f"duplicate architecture surface id: {surface_id}"
            )
        surface_ids.add(surface_id)

        covered_capabilities = [
            str(item)
            for item in as_list(
                surface.get("capabilities"),
                f"architecture surface {surface_id}.capabilities",
            )
        ]
        if not covered_capabilities:
            drift["architecture_surface_drift"].append(
                f"architecture surface {surface_id} has no capabilities"
            )
        for capability_id in covered_capabilities:
            if capability_id not in capability_ids:
                drift["architecture_surface_drift"].append(
                    f"architecture surface {surface_id} references unknown "
                    f"capability: {capability_id}"
                )
                continue
            previous = assigned_capabilities.get(capability_id)
            if previous is not None:
                drift["architecture_surface_drift"].append(
                    f"capability {capability_id} assigned to multiple "
                    f"architecture surfaces: {previous}, {surface_id}"
                )
            else:
                assigned_capabilities[capability_id] = surface_id

        required_paths = [
            str(item)
            for item in as_list(
                surface.get("required_paths"),
                f"architecture surface {surface_id}.required_paths",
            )
        ]
        if not required_paths:
            drift["architecture_surface_drift"].append(
                f"architecture surface {surface_id} has no required paths"
            )
        for rel in required_paths:
            declared_surface_paths.add(rel)
            if not resolve(root, rel).exists():
                drift["architecture_surface_drift"].append(
                    f"architecture surface {surface_id} required path "
                    f"missing: {rel}"
                )

        capability_docs: set[str] = set()
        for capability_id in covered_capabilities:
            capability_docs.update(
                capability_docs_by_id.get(capability_id, set())
            )
        canonical_docs = [
            str(item)
            for item in as_list(
                surface.get("canonical_docs"),
                f"architecture surface {surface_id}.canonical_docs",
            )
        ]
        if not canonical_docs:
            drift["architecture_surface_drift"].append(
                f"architecture surface {surface_id} has no canonical docs"
            )
        for rel in canonical_docs:
            if not resolve(root, rel).exists():
                drift["architecture_surface_drift"].append(
                    f"architecture surface {surface_id} canonical doc "
                    f"missing: {rel}"
                )
            if rel not in capability_docs:
                drift["architecture_surface_drift"].append(
                    f"architecture surface {surface_id} canonical doc is "
                    f"not declared by its Capability Map entries: {rel}"
                )

        validation_paths = [
            str(item)
            for item in as_list(
                surface.get("validation_paths"),
                f"architecture surface {surface_id}.validation_paths",
            )
        ]
        if not validation_paths:
            drift["architecture_surface_drift"].append(
                f"architecture surface {surface_id} has no validation paths"
            )
        for rel in validation_paths:
            validation_paths_seen.add(rel)
            if not resolve(root, rel).exists():
                drift["architecture_surface_drift"].append(
                    f"architecture surface {surface_id} validation path "
                    f"missing: {rel}"
                )
            elif not validation_path_is_bound(rel):
                drift["architecture_surface_drift"].append(
                    f"architecture surface {surface_id} validation path "
                    f"is not bound by Scenario Conformance or repository "
                    f"validator: {rel}"
                )

    unclassified_capabilities = sorted(
        capability_ids - set(assigned_capabilities)
    )
    for capability_id in unclassified_capabilities:
        drift["architecture_surface_drift"].append(
            f"Capability Map entry is not classified into an "
            f"architecture surface: {capability_id}"
        )

    architecture_summary = {
        "path": relative_path(root, architecture_inventory_path),
        "digest": (
            file_digest(architecture_inventory_path)
            if architecture_inventory_path.exists()
            else None
        ),
        "surface_count": len(surface_ids),
        "capability_count": len(capability_ids),
        "capability_accounted": len(
            capability_ids & set(assigned_capabilities)
        ),
        "unclassified_capabilities": unclassified_capabilities,
        "validation_path_count": len(validation_paths_seen),
        "validation_binding": "scenario_or_repository_validator",
    }

    discovery = as_mapping(
        config.get("surface_discovery"),
        "surface_discovery",
    )
    patterns = [
        str(item)
        for item in as_list(
            discovery.get("patterns"),
            "surface_discovery.patterns",
        )
    ]
    ignored = {
        str(item)
        for item in as_list(
            discovery.get("ignore"),
            "surface_discovery.ignore",
        )
    }
    discovered: set[str] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                discovered.add(path.relative_to(root).as_posix())
    for rel in sorted(discovered):
        if rel not in declared_surface_paths and rel not in ignored:
            drift["orphan_capability_surfaces"].append(
                f"unregistered discovered core surface: {rel}"
            )

    for index, raw_binding in enumerate(
        as_list(config.get("documentation_bindings"), "documentation_bindings")
    ):
        binding = as_mapping(
            raw_binding,
            f"documentation_bindings[{index}]",
        )
        source_rel = str(binding.get("source") or "")
        if not source_rel:
            drift["stale_documentation_links"].append(
                f"documentation binding {index} missing source"
            )
            continue
        source = resolve(root, source_rel)
        if not source.exists():
            drift["stale_documentation_links"].append(
                f"documentation source missing: {source_rel}"
            )
            continue
        source_text = source.read_text(encoding="utf-8")
        for raw_ref in as_list(
            binding.get("required_references"),
            f"documentation_bindings[{index}].required_references",
        ):
            rel = str(raw_ref)
            if not resolve(root, rel).exists():
                drift["stale_documentation_links"].append(
                    f"{source_rel} references missing target: {rel}"
                )
            elif rel not in source_text:
                drift["stale_documentation_links"].append(
                    f"{source_rel} missing canonical reference: {rel}"
                )

    drift["scenario_evidence_drift"].extend(
        run_scenario_conformance(
            root,
            scenario_helper,
            scenario_registry_path,
            scenario_dir,
        )
    )

    for index, raw_contract in enumerate(
        as_list(config.get("contract_files"), "contract_files")
    ):
        contract = as_mapping(
            raw_contract,
            f"contract_files[{index}]",
        )
        rel = str(contract.get("path") or "")
        if not rel:
            drift["workflow_contract_drift"].append(
                f"contract_files[{index}] missing path"
            )
            continue
        path = resolve(root, rel)
        if not path.exists():
            drift["workflow_contract_drift"].append(
                f"contract file missing: {rel}"
            )
            continue
        contract_text = path.read_text(encoding="utf-8")
        for raw_required in as_list(
            contract.get("required_strings"),
            f"contract_files[{index}].required_strings",
        ):
            required = str(raw_required)
            if required not in contract_text:
                drift["workflow_contract_drift"].append(
                    f"{rel} missing contract string: {required}"
                )

    for key in DRIFT_KEYS:
        drift[key] = sorted(set(drift[key]))

    workspace = repository_state(root)
    manifest = build_input_manifest(
        root,
        config_path,
        config,
        capability_map_path,
        capability_map,
        architecture_inventory_path,
        architecture_inventory,
        scenario_registry_path,
        scenario_dir,
        scenario_helper,
        discovered,
    )
    evidence_status = binding_status(workspace)
    revision_reproducible = (
        workspace.get("git_available") is True
        and workspace.get("dirty") is False
    )
    evidence_fingerprint = canonical_hash(
        {
            "repository_revision": workspace.get("head"),
            "workspace_status": evidence_status,
            "dirty_paths": workspace.get("dirty_paths") or [],
            "input_manifest_digest": manifest["digest"],
            "drift": drift,
        }
    )
    status = "PASS" if not any(drift.values()) else "DRIFT_DETECTED"

    return {
        "version": 1,
        "status": status,
        "repository_revision": workspace["head"],
        "workspace": workspace,
        "inputs": {
            "config": {
                "path": relative_path(root, config_path),
                "digest": file_digest(config_path),
            },
            "capability_map": {
                "path": relative_path(root, capability_map_path),
                "digest": file_digest(capability_map_path),
            },
            "architecture_surface_inventory": {
                "path": relative_path(root, architecture_inventory_path),
                "digest": (
                    file_digest(architecture_inventory_path)
                    if architecture_inventory_path.exists()
                    else None
                ),
            },
            "scenario_registry": {
                "path": relative_path(root, scenario_registry_path),
                "digest": file_digest(scenario_registry_path),
            },
            "manifest": manifest,
        },
        "evidence_binding": {
            "policy": {
                "manifest": "complete",
                "dirty_workspace": "report_non_reproducible",
            },
            "status": evidence_status,
            "revision_reproducible": revision_reproducible,
            "input_manifest_digest": manifest["digest"],
            "evidence_fingerprint": evidence_fingerprint,
        },
        "architecture_surfaces": architecture_summary,
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
        print(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(
            yaml.safe_dump(
                data,
                sort_keys=False,
                allow_unicode=True,
            ).rstrip()
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Deterministic AIPS repository health / "
            "architecture drift detector"
        )
    )
    parser.add_argument("command", choices=["audit"])
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument(
        "--config",
        default="config/repository-health.yaml",
    )
    parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config = Path(args.config)
    if not config.is_absolute():
        config = root / config

    try:
        data = analyze(root, config)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        workspace = repository_state(root)
        empty_manifest = {
            "count": 0,
            "digest": canonical_hash([]),
            "entries": [],
        }
        fallback_drift = {
            "missing_capability_targets": [],
            "architecture_surface_drift": [],
            "orphan_capability_surfaces": [],
            "stale_documentation_links": [],
            "scenario_evidence_drift": [],
            "workflow_contract_drift": [str(exc)],
        }
        evidence_status = binding_status(workspace)
        data = {
            "version": 1,
            "status": "DRIFT_DETECTED",
            "repository_revision": workspace["head"],
            "workspace": workspace,
            "inputs": {"manifest": empty_manifest},
            "evidence_binding": {
                "policy": {
                    "manifest": "unavailable",
                    "dirty_workspace": "report_non_reproducible",
                },
                "status": evidence_status,
                "revision_reproducible": (
                    workspace.get("git_available") is True
                    and workspace.get("dirty") is False
                ),
                "input_manifest_digest": empty_manifest["digest"],
                "evidence_fingerprint": canonical_hash(
                    {
                        "repository_revision": workspace.get("head"),
                        "workspace_status": evidence_status,
                        "dirty_paths": workspace.get("dirty_paths") or [],
                        "input_manifest_digest": empty_manifest["digest"],
                        "drift": fallback_drift,
                    }
                ),
            },
            "drift": fallback_drift,
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

    emit(data, args.format)
    return 0 if data.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
