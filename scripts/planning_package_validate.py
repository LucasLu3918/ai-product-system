#!/usr/bin/env python3
"""Deterministically validate a versioned AIPS Planning Package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from requirements_traceability import validate as validate_requirements  # noqa: E402

STATUSES = {"NOT_STARTED", "IN_PROGRESS", "NEEDS_DECISION", "READY_FOR_REVIEW", "APPROVED", "N/A", "STALE"}
APPLICABILITY = {"applicable", "not_applicable"}
DEPENDENCY_STRENGTHS = {"required", "recommended", "conditional"}
PACKAGE_STATUSES = {"DISCOVERY", "PLANNING", "REVIEW", "GATE_1_READY", "GATE_1_APPROVED", "IMPLEMENTATION_READY"}
ID_RE = re.compile(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)+\b")


def _load_yaml(path: Path, label: str, errors: list[str]) -> Any:
    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ValueError(f"duplicate key: {key!r}")
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    try:
        return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, UnicodeError, yaml.YAMLError, ValueError, TypeError) as exc:
        errors.append(f"{label}: cannot read YAML: {exc}")
        return None


def _artifact_path(root: Path, value: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}.path: expected a non-empty relative path")
        return None
    posix = PurePosixPath(value)
    if posix.is_absolute() or ".." in posix.parts or "\\" in value:
        errors.append(f"{label}.path: path must stay inside the package")
        return None
    candidate = (root / Path(*posix.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label}.path: resolved path escapes the package")
        return None
    return candidate


def _dependency(item: Any) -> tuple[str | None, str]:
    if isinstance(item, str):
        return item, "required"
    if isinstance(item, dict):
        return item.get("artifact"), str(item.get("strength", "required")).lower()
    return None, "required"


def validate_package(package: Path) -> dict[str, Any]:
    root = package.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = root / "PLANNING_MANIFEST.yaml"
    if not manifest_path.is_file():
        return {"status": "FAIL", "errors": ["PLANNING_MANIFEST.yaml: missing"], "warnings": [], "artifact_count": 0}

    doc = _load_yaml(manifest_path, "PLANNING_MANIFEST.yaml", errors)
    if not isinstance(doc, dict) or doc.get("version") != 1:
        errors.append("PLANNING_MANIFEST.yaml.version: expected 1")
        doc = {}
    product = doc.get("product")
    if not isinstance(product, dict) or not isinstance(product.get("name"), str) or not product.get("name", "").strip():
        errors.append("product.name: expected a non-empty name")
    planning_status = product.get("planning_status") if isinstance(product, dict) else None
    if planning_status not in PACKAGE_STATUSES:
        errors.append(f"product.planning_status: expected one of {', '.join(sorted(PACKAGE_STATUSES))}")

    raw_artifacts = doc.get("artifacts")
    if not isinstance(raw_artifacts, dict) or not raw_artifacts:
        errors.append("artifacts: expected a non-empty mapping")
        raw_artifacts = {}
    artifacts: dict[str, dict[str, Any]] = {}
    contents: dict[str, str] = {}
    for artifact_id, raw in raw_artifacts.items():
        label = f"artifacts.{artifact_id}"
        if not isinstance(artifact_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", artifact_id):
            errors.append(f"{label}: artifact ID must be a lowercase snake_case identifier")
        if not isinstance(raw, dict):
            errors.append(f"{label}: expected a mapping")
            continue
        applicability = raw.get("applicability")
        status = raw.get("status")
        if applicability not in APPLICABILITY:
            errors.append(f"{label}.applicability: expected applicable or not_applicable")
        if status not in STATUSES:
            errors.append(f"{label}.status: invalid status")
        if applicability == "not_applicable":
            if status != "N/A":
                errors.append(f"{label}.status: not_applicable artifacts must use N/A")
            if not isinstance(raw.get("reason"), str) or not raw.get("reason", "").strip():
                errors.append(f"{label}.reason: required when applicability is not_applicable")
        elif applicability == "applicable":
            if status == "N/A":
                errors.append(f"{label}.status: applicable artifacts cannot use N/A")
            path = _artifact_path(root, raw.get("path"), label, errors)
            if path is not None:
                if not path.is_file():
                    errors.append(f"{label}.path: artifact file does not exist")
                else:
                    try:
                        contents[artifact_id] = path.read_text(encoding="utf-8")
                    except (OSError, UnicodeError) as exc:
                        errors.append(f"{label}.path: artifact cannot be read as UTF-8: {exc}")
        dependencies = raw.get("depends_on", [])
        if not isinstance(dependencies, list):
            errors.append(f"{label}.depends_on: expected a list")
        artifacts[artifact_id] = raw

    graph: dict[str, list[str]] = {key: [] for key in artifacts}
    for artifact_id, raw in artifacts.items():
        dependencies = raw.get("depends_on", [])
        if not isinstance(dependencies, list):
            continue
        for index, dep in enumerate(dependencies):
            dep_id, strength = _dependency(dep)
            label = f"artifacts.{artifact_id}.depends_on[{index}]"
            if not isinstance(dep_id, str) or dep_id not in artifacts:
                errors.append(f"{label}: references an unknown artifact")
                continue
            if strength not in DEPENDENCY_STRENGTHS:
                errors.append(f"{label}.strength: expected required, recommended, or conditional")
                continue
            graph[artifact_id].append(dep_id)
            dep_item = artifacts[dep_id]
            if strength == "required" and dep_item.get("applicability") == "not_applicable":
                errors.append(f"{label}: required dependency {dep_id} is N/A")
            if raw.get("status") in {"READY_FOR_REVIEW", "APPROVED"} and strength == "required":
                if dep_item.get("status") not in {"READY_FOR_REVIEW", "APPROVED", "N/A"}:
                    errors.append(f"{label}: required dependency {dep_id} is not ready")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            errors.append(f"artifacts: dependency cycle includes {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for artifact_id in graph:
        visit(artifact_id)

    requirement_doc: Any = None
    requirement_artifact = artifacts.get("requirements")
    if isinstance(requirement_artifact, dict) and requirement_artifact.get("applicability") == "applicable":
        req_path = _artifact_path(root, requirement_artifact.get("path"), "artifacts.requirements", errors)
        if req_path is not None and req_path.is_file():
            requirement_doc = _load_yaml(req_path, "requirements", errors)
            if requirement_doc is not None:
                errors.extend(f"requirements: {issue}" for issue in validate_requirements(requirement_doc))

    id_sets: dict[str, set[str]] = {}
    for artifact_id, content in contents.items():
        id_sets[artifact_id] = set(ID_RE.findall(content))
    known_requirements: set[str] = set()
    known_acceptance: set[str] = set()
    if isinstance(requirement_doc, dict):
        for requirement in requirement_doc.get("requirements", []) or []:
            if not isinstance(requirement, dict):
                continue
            if isinstance(requirement.get("id"), str):
                known_requirements.add(requirement["id"])
            for criterion in requirement.get("acceptance_criteria", []) or []:
                if isinstance(criterion, dict) and isinstance(criterion.get("id"), str):
                    known_acceptance.add(criterion["id"])

    traceability = doc.get("traceability", [])
    if not isinstance(traceability, list):
        errors.append("traceability: expected a list")
        traceability = []
    mapped_requirements: set[str] = set()
    required_targets = {"experience_design": "SCR", "visual_system": "VIS", "domain_model": "DOM", "api_spec": "OP", "security": "SEC", "verification": None}
    for index, row in enumerate(traceability):
        label = f"traceability[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label}: expected a mapping")
            continue
        requirement_id = row.get("requirement_id")
        if not isinstance(requirement_id, str) or requirement_id not in known_requirements:
            errors.append(f"{label}.requirement_id: unknown requirement")
        elif requirement_id in mapped_requirements:
            errors.append(f"{label}.requirement_id: duplicate mapping for {requirement_id}")
        else:
            mapped_requirements.add(requirement_id)
        acceptance_ids = row.get("acceptance_ids")
        if not isinstance(acceptance_ids, list) or not acceptance_ids:
            errors.append(f"{label}.acceptance_ids: every mapped requirement needs acceptance criteria")
        elif any(value not in known_acceptance for value in acceptance_ids):
            errors.append(f"{label}.acceptance_ids: contains an unknown acceptance ID")
        downstream = row.get("downstream")
        if not isinstance(downstream, dict):
            errors.append(f"{label}.downstream: expected a mapping")
            continue
        for target, prefix in required_targets.items():
            link = downstream.get(target)
            target_label = f"{label}.downstream.{target}"
            if not isinstance(link, dict) or not isinstance(link.get("applicable"), bool):
                errors.append(f"{target_label}: declare applicable true/false")
                continue
            if not link["applicable"]:
                if not isinstance(link.get("reason"), str) or not link.get("reason", "").strip():
                    errors.append(f"{target_label}.reason: required when not applicable")
                continue
            refs = link.get("refs")
            if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
                errors.append(f"{target_label}.refs: applicable targets need non-empty references")
                continue
            if prefix is None:
                continue # Planned verification paths are not execution evidence.
            available_ids = id_sets.get(target, set())
            if not available_ids:
                errors.append(f"{target_label}: target artifact has no stable IDs")
            for ref in refs:
                if ref not in available_ids or not ref.startswith(prefix + "-"):
                    errors.append(f"{target_label}.refs: unknown {prefix} reference {ref}")

    if requirement_doc is not None:
        missing_mappings = sorted(known_requirements - mapped_requirements)
        for requirement_id in missing_mappings:
            errors.append(f"traceability: orphan requirement {requirement_id} has no mapping row")

    if planning_status == "GATE_1_READY":
        unfinished = [key for key, value in artifacts.items() if value.get("applicability") == "applicable" and value.get("status") not in {"READY_FOR_REVIEW", "APPROVED"}]
        if unfinished:
            errors.append("product.planning_status: GATE_1_READY requires every applicable artifact to be ready")
    approvals = doc.get("approvals", {})
    if planning_status in {"GATE_1_APPROVED", "IMPLEMENTATION_READY"}:
        planning = approvals.get("planning", {}) if isinstance(approvals, dict) else {}
        if not isinstance(planning, dict) or planning.get("status") != "APPROVED" or not isinstance(planning.get("evidence"), str) or not planning.get("evidence", "").strip():
            errors.append("approvals.planning: human approval evidence is required")
    if planning_status == "IMPLEMENTATION_READY":
        implementation = approvals.get("implementation", {}) if isinstance(approvals, dict) else {}
        if not isinstance(implementation, dict) or implementation.get("status") != "APPROVED" or not isinstance(implementation.get("evidence"), str) or not implementation.get("evidence", "").strip():
            errors.append("approvals.implementation: separate human approval evidence is required")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "artifact_count": len(artifacts),
        "requirement_count": len(known_requirements),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Planning Package directory")
    parser.add_argument("--format", choices=("text", "json", "yaml"), default="text")
    args = parser.parse_args()
    report = validate_package(args.package)
    if args.format == "json":
        print(json.dumps(report, sort_keys=True))
    elif args.format == "yaml":
        print(yaml.safe_dump(report, sort_keys=False, allow_unicode=True), end="")
    else:
        print(report["status"])
        for issue in report["errors"]:
            print(f"ERROR: {issue}")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
