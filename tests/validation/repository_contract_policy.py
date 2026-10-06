"""Strict reader for the parallel repository required-files policy."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


class RepositoryContractPolicyError(ValueError):
    """Raised when the repository contract policy is malformed or unsafe."""


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise RepositoryContractPolicyError("mapping keys must be scalar values") from exc
        if duplicate:
            raise RepositoryContractPolicyError(f"duplicate mapping key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def _validate_required_files(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise RepositoryContractPolicyError("required_files must be a non-empty list")

    paths: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item or item.strip() != item:
            raise RepositoryContractPolicyError("required_files entries must be non-empty trimmed strings")
        path = PurePosixPath(item)
        if (
            path.is_absolute()
            or item.startswith("~")
            or "\\" in item
            or ".." in path.parts
            or "." in path.parts
            or any(char in item for char in "*?[]")
            or re.match(r"^[A-Za-z]:", item)
        ):
            raise RepositoryContractPolicyError(f"required_files path must be a safe repository-relative file: {item}")
        normalized = path.as_posix()
        if normalized != item:
            raise RepositoryContractPolicyError(f"required_files path must be normalized: {item}")
        if item in seen:
            raise RepositoryContractPolicyError(f"duplicate required_files path: {item}")
        seen.add(item)
        paths.append(item)
    return paths


def parse_policy_text(text: str) -> list[str]:
    """Parse version-1 YAML and fail closed on unknown keys or unsafe entries."""
    try:
        document = yaml.load(text, Loader=_UniqueKeyLoader)
    except RepositoryContractPolicyError:
        raise
    except Exception as exc:
        raise RepositoryContractPolicyError(f"invalid YAML: {exc}") from exc

    if not isinstance(document, dict):
        raise RepositoryContractPolicyError("policy root must be a mapping")
    if set(document) != {"version", "required_files"}:
        raise RepositoryContractPolicyError("policy keys must be exactly version and required_files")
    if type(document["version"]) is not int or document["version"] != 1:
        raise RepositoryContractPolicyError("version must be integer 1")
    return _validate_required_files(document["required_files"])


def load_policy(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RepositoryContractPolicyError(f"cannot read policy: {path}: {exc}") from exc
    return parse_policy_text(text)


def missing_required_file_findings(paths: list[str], root: Path) -> list[str]:
    """Return stable missing-file diagnostics for a validated path list."""
    resolved_root = root.resolve()
    findings: list[str] = []
    for rel in paths:
        candidate = (resolved_root / rel).resolve()
        if not candidate.is_relative_to(resolved_root):
            raise RepositoryContractPolicyError(f"required_files path escapes repository: {rel}")
        if not candidate.exists():
            findings.append(f"Missing required file: {rel}")
    return findings
