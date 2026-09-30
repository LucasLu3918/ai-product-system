#!/usr/bin/env python3
"""Deterministic structural validation for Implementation Profiles and language profiles."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

RESOLUTIONS = {"confirmed", "strong_evidence", "inferred", "not_detected", "unresolved", "conflicting"}
AUTHORITIES = {"canonical", "descriptive", "proposed", "unresolved"}
LANGUAGES = {"go", "php", "python", "dotnet"}
OWNERSHIP = ("generated", "scaffolded", "project_owned", "unresolved")
QUALITY_RESULTS = {"PASS", "FAIL", "UNVERIFIED", "BLOCKED"}
PROFILE_SECTIONS = (
    "identity", "detection", "runtime", "package_model", "dependency_management",
    "formatting", "static_analysis", "error_handling", "testing", "concurrency",
    "resource_management", "security", "precedence",
)


def _mapping(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{label} must be a mapping")
        return {}
    return value


def _list(value: Any, label: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    return value


def _evidence(value: Any, label: str, errors: list[str], required: bool = False) -> list[Any]:
    items = _list(value, label, errors)
    if required and not items:
        errors.append(f"{label} is required for a resolved decision")
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] must record source provenance")
            continue
        if not any(isinstance(item.get(k), str) and item[k].strip() for k in ("source", "reference", "command", "url")):
            errors.append(f"{label}[{index}] requires source, reference, command, or url")
    return items


def _decision(value: Any, label: str, errors: list[str], *, level_key: str | None = None) -> dict[str, Any]:
    item = _mapping(value, label, errors)
    resolution = item.get("resolution")
    if resolution not in RESOLUTIONS:
        errors.append(f"{label}.resolution must be one of {sorted(RESOLUTIONS)}")
    evidence = _evidence(item.get("evidence"), f"{label}.evidence", errors,
                         required=resolution in {"confirmed", "strong_evidence", "inferred"})
    if level_key and resolution == "not_detected" and item.get(level_key) != "unknown":
        errors.append(f"{label}.resolution=not_detected requires {level_key}=unknown; not_detected is not none")
    if resolution == "confirmed" and evidence and not any(
        str(e.get("source", "")).lower() in {"human", "user", "human_decision", "repository"}
        or e.get("reference") for e in evidence if isinstance(e, dict)
    ):
        errors.append(f"{label}.confirmed requires decision evidence")
    return item


def _owned_path(entry: Any, label: str, errors: list[str]) -> str | None:
    path = entry.get("path") if isinstance(entry, dict) else entry
    if not isinstance(path, str) or not path.strip():
        errors.append(f"{label} must be a non-empty repository-relative path")
        return None
    raw = path.strip()
    pure = PurePosixPath(raw)
    if "\\" in raw or pure.is_absolute() or any(part in {"", ".", ".."} for part in raw.split("/")) or pure.as_posix() != raw:
        errors.append(f"{label} must be a normalized repository-relative path")
        return None
    return pure.as_posix()


def validate_language_profile(doc: Any) -> list[str]:
    errors: list[str] = []
    root = _mapping(doc, "language_profile", errors)
    if str(root.get("schema_version")) != "1":
        errors.append("language_profile.schema_version must be '1'")
    identity = _mapping(root.get("identity"), "identity", errors)
    language = identity.get("language")
    if language not in LANGUAGES:
        errors.append(f"identity.language must be one of {sorted(LANGUAGES)}")
    for section in PROFILE_SECTIONS:
        value = _mapping(root.get(section), section, errors)
        if section in {"detection", "formatting", "static_analysis", "error_handling", "testing", "concurrency", "resource_management", "security"}:
            key = "manifests" if section == "detection" else ("inherit" if section == "security" else "baseline" if section in {"formatting", "static_analysis", "testing"} else "guidance")
            if not isinstance(value.get(key), list):
                errors.append(f"{section}.{key} must be a list")
    runtime = _mapping(root.get("runtime"), "runtime", errors)
    if not isinstance(runtime.get("version_source"), list):
        errors.append("runtime.version_source must be a list")
    package_model = _mapping(root.get("package_model"), "package_model", errors)
    if not isinstance(package_model.get("guidance"), str) or not package_model["guidance"].strip():
        errors.append("package_model.guidance must be a non-empty string")
    dependencies = _mapping(root.get("dependency_management"), "dependency_management", errors)
    if not isinstance(dependencies.get("native"), list):
        errors.append("dependency_management.native must be a list")
    for section in ("error_handling", "concurrency", "resource_management"):
        section_value = _mapping(root.get(section), section, errors)
        if not isinstance(section_value.get("guidance"), list):
            errors.append(f"{section}.guidance must be a list")
    security = _mapping(root.get("security"), "security", errors)
    if not isinstance(security.get("inherit"), list):
        errors.append("security.inherit must be a list")
    precedence = root.get("precedence") or {}
    if not isinstance(precedence, dict) or precedence.get("preserve_project_native") is not True:
        errors.append("precedence.preserve_project_native must be true")
    defaults = precedence.get("framework_or_library_defaults") if isinstance(precedence, dict) else None
    if defaults != []:
        errors.append("framework_or_library_defaults must be empty in a language profile")
    return errors


def validate_profile(doc: Any) -> dict[str, Any]:
    errors: list[str] = []
    root = _mapping(doc, "profile", errors)
    if str(root.get("schema_version")) != "1":
        errors.append("schema_version must be '1'")

    project = _mapping(root.get("project"), "project", errors)
    if project.get("mode") not in {"existing", "new"}:
        errors.append("project.mode must be existing or new")
    _evidence(project.get("evidence"), "project.evidence", errors)

    contract = _mapping(root.get("contract"), "contract", errors)
    if contract.get("authority") not in AUTHORITIES:
        errors.append(f"contract.authority must be one of {sorted(AUTHORITIES)}")
    if contract.get("type") not in {"openapi", "none", "other"}:
        errors.append("contract.type must be openapi, none, or other")
    if not isinstance(contract.get("affects_change"), bool):
        errors.append("contract.affects_change must be boolean")
    if contract.get("resolution") not in RESOLUTIONS:
        errors.append(f"contract.resolution must be one of {sorted(RESOLUTIONS)}")
    _evidence(contract.get("evidence"), "contract.evidence", errors,
              required=contract.get("resolution") in {"confirmed", "strong_evidence", "inferred"})
    openapi_evidence = contract.get("openapi")
    if openapi_evidence is not None:
        openapi_evidence = _mapping(openapi_evidence, "contract.openapi", errors)
        if openapi_evidence.get("validation_status") not in QUALITY_RESULTS:
            errors.append("contract.openapi.validation_status is invalid")
        if openapi_evidence.get("compatibility_status") not in {"NO_CHANGE", "NON_BREAKING", "BREAKING", "UNKNOWN", "BLOCKED"}:
            errors.append("contract.openapi.compatibility_status is invalid")
        if openapi_evidence.get("implementation_conformance_status") not in QUALITY_RESULTS:
            errors.append("contract.openapi.implementation_conformance_status is invalid")
        if openapi_evidence.get("baseline_authority") not in AUTHORITIES:
            errors.append("contract.openapi.baseline_authority is invalid")
        if not isinstance(openapi_evidence.get("compatibility_required"), bool):
            errors.append("contract.openapi.compatibility_required must be boolean")
        for key, status_key in (("validation_report", "validation_status"),
                                ("compatibility_report", "compatibility_status"),
                                ("conformance_report", "implementation_conformance_status")):
            reference = openapi_evidence.get(key)
            if reference is not None and (not isinstance(reference, str) or not reference.strip() or reference.startswith("/") or ".." in reference.split("/")):
                errors.append(f"contract.openapi.{key} must be a repository-relative path")
            if openapi_evidence.get(status_key) in {"PASS", "NO_CHANGE", "NON_BREAKING"} and not reference:
                errors.append(f"contract.openapi.{key} is required for a passing status")
        spec_digest = openapi_evidence.get("spec_sha256")
        if spec_digest is not None and (not isinstance(spec_digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", spec_digest)):
            errors.append("contract.openapi.spec_sha256 must be sha256:<64 lowercase hex>")
        if openapi_evidence.get("validation_status") == "PASS" and not spec_digest:
            errors.append("a passing OpenAPI validation requires spec_sha256")
        if openapi_evidence.get("baseline_authority") != "canonical" and openapi_evidence.get("compatibility_status") in {"NO_CHANGE", "NON_BREAKING", "BREAKING"}:
            errors.append("compatibility status requires a canonical baseline authority")

    technology = _mapping(root.get("technology"), "technology", errors)
    language = _mapping(technology.get("language"), "technology.language", errors)
    if language.get("name") not in LANGUAGES:
        errors.append(f"technology.language.name must be one of {sorted(LANGUAGES)}")
    if language.get("resolution") not in RESOLUTIONS:
        errors.append("technology.language.resolution is invalid")
    _evidence(language.get("evidence"), "technology.language.evidence", errors,
              required=language.get("resolution") in {"confirmed", "strong_evidence", "inferred"})
    framework = _mapping(technology.get("framework"), "technology.framework", errors)
    if framework.get("resolution") not in RESOLUTIONS:
        errors.append("technology.framework.resolution is invalid")
    _evidence(framework.get("evidence"), "technology.framework.evidence", errors,
              required=framework.get("resolution") in {"confirmed", "strong_evidence", "inferred"})
    if framework.get("resolution") in {"confirmed", "strong_evidence", "inferred"} and not (isinstance(framework.get("name"), str) and framework["name"].strip()):
        errors.append("resolved technology.framework requires a name")
    decision_record = _mapping(technology.get("decision_record"), "technology.decision_record", errors)
    if not isinstance(decision_record.get("constraints"), list) or not isinstance(decision_record.get("candidates"), list):
        errors.append("technology.decision_record constraints and candidates must be lists")
    if not isinstance(decision_record.get("confirmed"), bool):
        errors.append("technology.decision_record.confirmed must be boolean")
    if decision_record.get("selected_by") not in {"project_evidence", "human"}:
        errors.append("technology.decision_record.selected_by must be project_evidence or human")
    for key in ("human_preferences",):
        if not isinstance(decision_record.get(key), list):
            errors.append(f"technology.decision_record.{key} must be a list")

    architecture = _mapping(root.get("architecture"), "architecture", errors)
    for key, level_key in (("logical_style", "value"), ("clean_architecture", "level"), ("deployment", "style")):
        _decision(architecture.get(key), f"architecture.{key}", errors, level_key=level_key)
    allowed_levels = {
        "logical_style": {"simple", "modular", "modular_monolith", "domain_oriented", "domain_ecosystem", "unknown"},
        "clean_architecture": {"none", "light", "full", "unknown"},
        "deployment": {"single_deployment", "modular_monolith", "microservices", "serverless", "unknown"},
    }
    for key, allowed in allowed_levels.items():
        item = _mapping(architecture.get(key), f"architecture.{key}", errors)
        value_key = "value" if key == "logical_style" else "level" if key == "clean_architecture" else "style"
        if item.get(value_key) not in allowed:
            errors.append(f"architecture.{key}.{value_key} must be one of {sorted(allowed)}")
    if not isinstance(architecture.get("complexity_signals"), list) or not isinstance(architecture.get("triggers"), list) or not isinstance(architecture.get("counter_signals"), list):
        errors.append("architecture complexity_signals, triggers, and counter_signals must be lists")
    ddd = _mapping(architecture.get("ddd"), "architecture.ddd", errors)
    for key in ("tactical", "strategic"):
        item = _decision(ddd.get(key), f"architecture.ddd.{key}", errors, level_key="level")
        allowed = {"none", "selective", "tactical", "unknown"} if key == "tactical" else {"none", "selective", "strategic", "unknown"}
        if item.get("level") not in allowed:
            errors.append(f"architecture.ddd.{key}.level must be one of {sorted(allowed)}")

    generation = _mapping(root.get("generation"), "generation", errors)
    if not isinstance(generation.get("enabled"), bool):
        errors.append("generation.enabled must be boolean")
    if generation.get("policy") not in {"none", "boundary_only"}:
        errors.append("generation.policy must be none or boundary_only")
    if generation.get("enabled") is False and generation.get("policy") != "none":
        errors.append("disabled generation requires policy=none")

    ownership = _mapping(root.get("ownership"), "ownership", errors)
    seen_paths: dict[str, str] = {}
    for group in OWNERSHIP:
        entries = _list(ownership.get(group), f"ownership.{group}", errors)
        group_seen: set[str] = set()
        for index, entry in enumerate(entries):
            path = _owned_path(entry, f"ownership.{group}[{index}]", errors)
            if path is None:
                continue
            if path in group_seen:
                errors.append(f"ownership.{group} duplicates path {path}")
            group_seen.add(path)
            previous = seen_paths.get(path)
            if previous and previous != group:
                errors.append(f"ownership path {path} overlaps {previous} and {group}")
            seen_paths[path] = group

    quality = _mapping(root.get("quality"), "quality", errors)
    for key in ("mandatory", "project_required", "risk_triggered", "advisory", "evidence"):
        entries = _list(quality.get(key), f"quality.{key}", errors)
        if key == "evidence":
            for index, item in enumerate(entries):
                row = _mapping(item, f"quality.evidence[{index}]", errors)
                if row.get("status") not in QUALITY_RESULTS:
                    errors.append(f"quality.evidence[{index}].status must be one of {sorted(QUALITY_RESULTS)}")
                if not any(isinstance(row.get(k), str) and row[k].strip() for k in ("source", "command", "reference")):
                    errors.append(f"quality.evidence[{index}] requires source/command/reference provenance")

    knowledge = _mapping(root.get("knowledge"), "knowledge", errors)
    _evidence(knowledge.get("project_evidence"), "knowledge.project_evidence", errors)
    _evidence(knowledge.get("external_evidence"), "knowledge.external_evidence", errors)

    unresolved = _list(root.get("unresolved"), "unresolved", errors)
    ids: set[str] = set()
    blocking = False
    for index, item in enumerate(unresolved):
        row = _mapping(item, f"unresolved[{index}]", errors)
        for key in ("id", "topic", "description", "resolution"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                errors.append(f"unresolved[{index}].{key} is required")
        if row.get("id") in ids:
            errors.append(f"unresolved duplicates id {row.get('id')}")
        ids.add(row.get("id"))
        if not isinstance(row.get("blocking"), bool):
            errors.append(f"unresolved[{index}].blocking must be boolean")
        blocking = blocking or row.get("blocking") is True
        _evidence(row.get("evidence"), f"unresolved[{index}].evidence", errors)

    blocked = blocking or (contract.get("authority") == "unresolved" and contract.get("affects_change") is True)
    openapi_blocked = False
    if contract.get("type") == "openapi" and contract.get("affects_change") is True and isinstance(contract.get("openapi"), dict):
        oas = contract["openapi"]
        if contract.get("authority") in {"canonical", "proposed"} and oas.get("validation_status") != "PASS":
            openapi_blocked = True
        if oas.get("compatibility_required") is True and (
            oas.get("baseline_authority") != "canonical"
            or oas.get("compatibility_status") not in {"NO_CHANGE", "NON_BREAKING"}
        ):
            openapi_blocked = True
        if oas.get("implementation_conformance_status") in {"FAIL", "BLOCKED"}:
            openapi_blocked = True
    blocked = blocked or openapi_blocked
    blocked = blocked or (project.get("mode") == "new" and decision_record.get("confirmed") is not True)
    declared_status = root.get("status")
    if declared_status not in {"READY", "BLOCKED"}:
        errors.append("status must be READY or BLOCKED")
    if declared_status == "READY" and blocked:
        errors.append("status=READY conflicts with unresolved decisions, invalid/missing authoritative OpenAPI evidence, required compatibility review, or unconfirmed new-project decisions")
    if declared_status == "BLOCKED" and not blocked:
        errors.append("status=BLOCKED requires an unresolved decision, affected unresolved contract authority, required OpenAPI evidence, failed conformance, or unconfirmed new-project decision")
    return {
        "structural_status": "FAIL" if errors else "PASS",
        "implementation_status": "BLOCKED" if blocked else "READY",
        "errors": errors,
    }


def _load(path: Path) -> tuple[Any, str | None]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}, None
    except (OSError, yaml.YAMLError) as exc:
        return None, f"{path}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="Implementation Profile YAML")
    parser.add_argument("--language-profile", type=Path, help="Optional language profile to validate alongside the Implementation Profile")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    doc, load_error = _load(args.profile)
    result = validate_profile(doc) if load_error is None else {"structural_status": "FAIL", "implementation_status": "UNKNOWN", "errors": [load_error]}
    if args.language_profile:
        language_doc, language_error = _load(args.language_profile)
        if language_error:
            result["errors"].append(language_error)
        else:
            result["errors"].extend(validate_language_profile(language_doc))
        if result["errors"]:
            result["structural_status"] = "FAIL"
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"STRUCTURAL {result['structural_status']} — IMPLEMENTATION {result['implementation_status']}")
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
    if result["structural_status"] == "FAIL":
        return 1
    return 2 if result["implementation_status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
