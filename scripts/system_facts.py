#!/usr/bin/env python3
"""Validate and render deterministic factual reference tables from AIPS registries."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

import yaml

START = "<!-- AIPS-SYSTEM-FACTS:BEGIN -->"
END = "<!-- AIPS-SYSTEM-FACTS:END -->"
DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise TypeError(f"{path}: expected a mapping")
    return data


def validate_facts(root: Path, facts: dict[str, Any] | None = None) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    try:
        facts = facts or read_yaml(root / "config/system-facts.yaml")
        surfaces = read_yaml(root / "config/architecture-surfaces.yaml").get("surfaces") or []
    except (OSError, yaml.YAMLError, ValueError) as exc:
        return [str(exc)]
    if facts.get("version") != 1:
        errors.append("system facts version must be 1")
    python = facts.get("python") or {}
    supported = str(python.get("supported") or "")
    tested = str(python.get("ci_tested") or "")
    compatibility_tested = [str(item) for item in python.get("ci_compatibility_tested") or []]
    if not re.fullmatch(r">=3\.\d+(?:,<\d+(?:\.\d+)?)?", supported):
        errors.append("python.supported must be a bounded or open Python compatibility range")
    if not re.fullmatch(r"3\.\d+", tested):
        errors.append("python.ci_tested must be a Python major.minor version")
    if not compatibility_tested or len(compatibility_tested) != len(set(compatibility_tested)):
        errors.append("python.ci_compatibility_tested must be a non-empty list of unique Python versions")
    if any(not re.fullmatch(r"3\.\d+", item) for item in compatibility_tested):
        errors.append("python.ci_compatibility_tested entries must be Python major.minor versions")
    baseline_match = re.match(r">=3\.(\d+)", supported)
    if baseline_match:
        minimum_minor = int(baseline_match.group(1))
        if tested not in compatibility_tested:
            errors.append("python.ci_tested must appear in python.ci_compatibility_tested")
        if any(int(item.split(".")[1]) < minimum_minor for item in compatibility_tested if re.fullmatch(r"3\.\d+", item)):
            errors.append("python.ci_compatibility_tested cannot include versions below python.supported")
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        try:
            project_config = tomllib.loads(text).get("tool", {}).get("aips", {})
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"pyproject.toml is invalid: {exc}")
            project_config = {}
        if project_config.get("python_supported") != supported:
            errors.append("pyproject.toml tool.aips.python_supported must match config/system-facts.yaml")
        if project_config.get("python_tested") != tested:
            errors.append("pyproject.toml mypy python_version must match the CI tested Python version")
        if project_config.get("python_compatibility_tested") != compatibility_tested:
            errors.append("pyproject.toml tool.aips.python_compatibility_tested must match config/system-facts.yaml")
        syntax_baseline = re.search(r">=3\.(\d+)", supported)
        if not syntax_baseline or f'target-version = "py3{syntax_baseline.group(1)}"' not in text:
            errors.append("pyproject.toml Ruff target-version must match the supported Python syntax baseline")
    surface_ids = {str(item.get("id")) for item in surfaces if isinstance(item, dict)}
    commands = facts.get("commands")
    if not isinstance(commands, list) or not commands:
        return errors + ["commands must be a non-empty list"]
    seen: set[str] = set()
    for index, row in enumerate(commands):
        label = f"commands[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} must be a mapping")
            continue
        identifier = str(row.get("id") or "")
        if not identifier or identifier in seen:
            errors.append(f"{label}.id must be unique and non-empty")
        seen.add(identifier)
        if not re.fullmatch(r"aips(?: [a-z][a-z0-9-]*)*", str(row.get("command") or "")):
            errors.append(f"{label}.command must be a public AIPS command")
        refs = row.get("surfaces") or []
        if not refs or any(reference not in surface_ids for reference in refs):
            errors.append(f"{label}.surfaces must reference known architecture surfaces")
        if not row.get("platforms") or not row.get("runtime_requirement"):
            errors.append(f"{label} must state platforms and runtime_requirement")
        for key in ("validation_bindings", "documentation_bindings", "optional_dependencies"):
            values = row.get(key)
            if not isinstance(values, list):
                errors.append(f"{label}.{key} must be a list")
                continue
            if key != "optional_dependencies":
                for relative in values:
                    path = (root / str(relative)).resolve()
                    if not path.is_relative_to(root) or not path.is_file():
                        errors.append(f"{label}.{key} references a missing or out-of-root file: {relative}")
            elif any(Path(str(value)).is_absolute() or ".." in Path(str(value)).parts for value in values):
                errors.append(f"{label}.optional_dependencies must use repository-relative names")
    if len(seen) != len(commands):
        errors.append("command identifiers must be unique")
    return errors


def _cell(value: Any) -> str:
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def generated_block(root: Path, facts: dict[str, Any] | None = None) -> str:
    facts = facts or read_yaml(root / "config/system-facts.yaml")
    arch = read_yaml(root / "config/architecture-surfaces.yaml")
    surfaces = {item["id"]: item for item in arch.get("surfaces") or []}
    lines = [
        START,
        "## Public commands",
        "",
        "| Command | Capabilities | Platforms | Runtime | Optional dependencies | Validation | Documentation |",
        "|---|---|---|---|---|---|---|",
    ]
    for command in facts["commands"]:
        capabilities = []
        for surface_id in command["surfaces"]:
            capabilities.extend(surfaces[surface_id].get("capabilities") or [])
        values = (
            f"`{command['command']}`",
            _cell(sorted(set(capabilities))),
            _cell(command["platforms"]),
            _cell(command["runtime_requirement"]),
            _cell(command.get("optional_dependencies") or ["None"]),
            _cell(command["validation_bindings"]),
            _cell(command["documentation_bindings"]),
        )
        lines.append("| " + " | ".join(values) + " |")
    lines.extend([
        "",
        "## Capability surfaces",
        "",
        "| Surface | Capabilities | Canonical documentation | Validation bindings |",
        "|---|---|---|---|",
    ])
    for surface in arch.get("surfaces") or []:
        values = (
            f"`{surface['id']}`",
            _cell(surface.get("capabilities") or []),
            _cell(surface.get("canonical_docs") or []),
            _cell(surface.get("validation_paths") or []),
        )
        lines.append("| " + " | ".join(values) + " |")
    lines.extend([
        "",
        "## Runtime support",
        "",
        f"- Supported Python: `{facts['python']['supported']}`",
        f"- CI tested Python: `{facts['python']['ci_tested']}`",
        f"- CI compatibility smoke-tested Python: `{', '.join(facts['python']['ci_compatibility_tested'])}`",
        f"- CI tested Node.js: `{facts['python']['node_tested']}`",
        END,
    ])
    return "\n".join(lines)


def update_document(root: Path, *, check: bool) -> bool:
    path = root / "docs/human/SYSTEM_REFERENCE.md"
    if path.is_file():
        current = path.read_text(encoding="utf-8")
    else:
        current = (
            "# AIPS System Reference\n\n"
            "This page lists factual command, capability and runtime data. "
            "Explanatory policy remains in the linked canonical documentation.\n\n"
            f"{START}\n{END}\n"
        )
    if current.count(START) != 1 or current.count(END) != 1:
        print("system reference must contain exactly one generated block", file=sys.stderr)
        return False
    begin = current.index(START)
    finish = current.index(END, begin) + len(END)
    desired = current[:begin] + generated_block(root) + current[finish:]
    if check:
        if current != desired:
            print("SYSTEM_REFERENCE.md generated facts are stale", file=sys.stderr)
            return False
        return True
    path.write_text(desired, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    errors = validate_facts(args.root)
    if errors:
        print("SYSTEM FACTS INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    if not update_document(args.root, check=args.check):
        return 1
    print("SYSTEM FACTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
