#!/usr/bin/env python3
"""Deterministically audit external Agent/provider credential dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

import yaml


class GuardError(ValueError):
    pass


SECRET_REF = re.compile(r"secrets\.([A-Z][A-Z0-9_]*)")
CONFIG_REF = re.compile(r"(?m)^\s*(?:credential_secret|required_secret)\s*:\s*([A-Z][A-Z0-9_]*)\s*$")
PYTHON_ENV_REF = re.compile(
    r"os\.(?:environ\.get|getenv)\(\s*['\"]([A-Z][A-Z0-9_]*_API_KEY)['\"]"
)


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise GuardError(f"{path}: expected mapping")
    return value


def validate_config(config: dict[str, Any]) -> None:
    if config.get("version") != 1:
        raise GuardError("config.version must be 1")

    policy = config.get("policy") or {}
    if policy.get("external_credentials_required_for_baseline") is not False:
        raise GuardError("external credentials must not be required for baseline AIPS")
    if policy.get("external_credentials_required_for_release") is not False:
        raise GuardError("external credentials must not be required for release")
    if policy.get("undeclared_external_credential") != "BLOCK":
        raise GuardError("undeclared external credentials must BLOCK")
    if policy.get("pull_request_secret_exposure") != "BLOCK":
        raise GuardError("pull-request secret exposure must BLOCK")
    if policy.get("credential_values_in_repository") is not False:
        raise GuardError("credential values must not be stored in the repository")

    scope = config.get("scope") or {}
    roots = scope.get("scan_roots")
    suffixes = scope.get("file_suffixes")
    if not isinstance(roots, list) or not roots:
        raise GuardError("scope.scan_roots must be a non-empty list")
    if not isinstance(suffixes, list) or not suffixes:
        raise GuardError("scope.file_suffixes must be a non-empty list")

    credentials = config.get("credentials")
    if not isinstance(credentials, dict) or not credentials:
        raise GuardError("credentials must be a non-empty mapping")

    for name, entry in credentials.items():
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", str(name)):
            raise GuardError(f"invalid credential name: {name}")
        if not isinstance(entry, dict):
            raise GuardError(f"{name}: entry must be a mapping")
        if entry.get("class") != "external_agent_provider":
            raise GuardError(f"{name}: class must remain external_agent_provider")
        if entry.get("optional") is not True:
            raise GuardError(f"{name}: external Agent/provider credential must remain optional")
        if entry.get("activation") != "explicit_secret_configuration":
            raise GuardError(f"{name}: activation must require explicit secret configuration")
        if entry.get("required_for_baseline") is not False:
            raise GuardError(f"{name}: must not be required for baseline")
        if entry.get("required_for_release") is not False:
            raise GuardError(f"{name}: must not be required for release")
        behaviors = entry.get("missing_behaviors")
        if not isinstance(behaviors, list) or not behaviors or not all(isinstance(x, str) and x.strip() for x in behaviors):
            raise GuardError(f"{name}: missing_behaviors must be non-empty strings")
        consumers = entry.get("allowed_consumers")
        if not isinstance(consumers, list) or not consumers or len(set(consumers)) != len(consumers):
            raise GuardError(f"{name}: allowed_consumers must be unique and non-empty")

    for item in config.get("conditional_workflow_exposure") or []:
        if not isinstance(item, dict):
            raise GuardError("conditional_workflow_exposure items must be mappings")
        if item.get("credential") not in credentials:
            raise GuardError("conditional workflow exposure references undeclared credential")
        if not str(item.get("workflow") or "").startswith(".github/workflows/"):
            raise GuardError("conditional workflow exposure must target a workflow")
        if not str(item.get("required_condition") or "").strip():
            raise GuardError("conditional workflow exposure requires a condition")

    authority = config.get("authority") or {}
    if not isinstance(authority, dict) or any(value is not False for value in authority.values()):
        raise GuardError("credential guard grants no protected authority")


def _candidate_files(root: Path, config: dict[str, Any]) -> list[Path]:
    suffixes = set(str(x) for x in (config.get("scope") or {}).get("file_suffixes") or [])
    files: list[Path] = []
    for rel in (config.get("scope") or {}).get("scan_roots") or []:
        base = root / str(rel)
        if not base.exists():
            continue
        if base.is_file():
            if base.suffix in suffixes:
                files.append(base)
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in suffixes:
                files.append(path)
    return sorted(set(files))


def discover(root: Path, config: dict[str, Any]) -> dict[str, list[str]]:
    discovered: dict[str, set[str]] = {}
    for path in _candidate_files(root, config):
        text = path.read_text(encoding="utf-8")
        names = set(SECRET_REF.findall(text))
        names.update(CONFIG_REF.findall(text))
        names.update(PYTHON_ENV_REF.findall(text))
        if not names:
            continue
        rel = path.relative_to(root).as_posix()
        for name in names:
            discovered.setdefault(name, set()).add(rel)
    return {name: sorted(paths) for name, paths in sorted(discovered.items())}


def _workflow_has_pull_request(text: str) -> bool:
    return re.search(r"(?m)^\s*pull_request(?:_target)?\s*:", text) is not None


def _authority() -> dict[str, bool]:
    return {
        "human_approval_granted": False,
        "merge_authorized": False,
        "release_authorized": False,
        "publication_authorized": False,
        "credential_creation_authorized": False,
    }


def audit(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    try:
        validate_config(config)
    except GuardError as exc:
        return {
            "version": 1,
            "status": "BLOCKED",
            "findings": [str(exc)],
            "discovered_credentials": {},
            "authority": _authority(),
        }

    discovered = discover(root, config)
    declared = config["credentials"]

    for name in sorted(set(discovered) - set(declared)):
        findings.append(f"undeclared external credential dependency: {name}")

    for name, entry in declared.items():
        actual = set(discovered.get(name, []))
        allowed = set(str(x) for x in entry.get("allowed_consumers") or [])
        for path in sorted(actual - allowed):
            findings.append(f"{name}: undeclared consumer: {path}")
        for path in sorted(allowed - actual):
            findings.append(f"{name}: declared consumer is not observed: {path}")

        for path in sorted(actual):
            if not path.startswith(".github/workflows/"):
                continue
            workflow = root / path
            if workflow.exists() and _workflow_has_pull_request(workflow.read_text(encoding="utf-8")):
                findings.append(f"{name}: workflow exposes external credential on pull_request surface: {path}")

    for exposure in config.get("conditional_workflow_exposure") or []:
        name = str(exposure["credential"])
        path = str(exposure["workflow"])
        condition = str(exposure["required_condition"])
        workflow = root / path
        if not workflow.exists():
            findings.append(f"{name}: conditional workflow missing: {path}")
            continue
        lines = workflow.read_text(encoding="utf-8").splitlines()
        secret_lines = [i for i, line in enumerate(lines) if f"secrets.{name}" in line]
        if not secret_lines:
            findings.append(f"{name}: conditional workflow has no secret reference: {path}")
            continue
        for index in secret_lines:
            window = "\n".join(lines[max(0, index - 8): index + 1])
            if condition not in window:
                findings.append(f"{name}: secret exposure is not guarded by explicit provider condition in {path}")

    return {
        "version": 1,
        "status": "PASS" if not findings else "BLOCKED",
        "policy": {
            "external_credentials_required_for_baseline": False,
            "external_credentials_required_for_release": False,
        },
        "discovered_credentials": discovered,
        "findings": findings,
        "authority": _authority(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    audit_cmd = sub.add_parser("audit")
    audit_cmd.add_argument("--config", required=True, type=Path)
    audit_cmd.add_argument("--root", default=".", type=Path)
    audit_cmd.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        config = load_yaml(args.config)
        result = audit(args.root.resolve(), config)
    except (OSError, yaml.YAMLError, GuardError) as exc:
        result = {
            "version": 1,
            "status": "BLOCKED",
            "findings": [str(exc)],
            "discovered_credentials": {},
            "authority": _authority(),
        }

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
