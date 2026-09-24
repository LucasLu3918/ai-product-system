#!/usr/bin/env python3
"""Validate the structure and ID links in an optional Planning Package requirements registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

import yaml


PATTERNS = {"ubiquitous", "event_driven", "state_driven", "optional_feature", "unwanted_behavior", "complex"}
KINDS = {"functional", "non_functional"}
ID_RE = re.compile(r"^(?:FR|NFR)-\d{3,}$")
AC_ID_RE = re.compile(r"^AC-\d{3,}$")
EARS_FORMS = {
    "ubiquitous": re.compile(r"^the .+ shall .+$", re.IGNORECASE),
    "event_driven": re.compile(r"^when .+, the .+ shall .+$", re.IGNORECASE),
    "state_driven": re.compile(r"^while .+, the .+ shall .+$", re.IGNORECASE),
    "optional_feature": re.compile(r"^where .+, the .+ shall .+$", re.IGNORECASE),
    "unwanted_behavior": re.compile(r"^if .+, then the .+ shall .+$", re.IGNORECASE),
    "complex": re.compile(r"^while .+, when .+, the .+ shall .+$", re.IGNORECASE),
}


def validate(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict) or document.get("version") != 1:
        return ["version: expected mapping with version: 1"]
    requirements = document.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        return ["requirements: expected a non-empty list"]

    requirement_ids: set[str] = set()
    acceptance_ids: set[str] = set()
    for index, item in enumerate(requirements):
        label = f"requirements[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label}: expected mapping")
            continue
        req_id = item.get("id")
        if not isinstance(req_id, str) or not ID_RE.fullmatch(req_id):
            errors.append(f"{label}.id: expected FR-NNN or NFR-NNN")
        elif req_id in requirement_ids:
            errors.append(f"{label}.id: duplicate {req_id}")
        else:
            requirement_ids.add(req_id)

        kind = item.get("kind")
        if kind not in KINDS:
            errors.append(f"{label}.kind: expected functional or non_functional")
        elif isinstance(req_id, str) and kind == "functional" and not req_id.startswith("FR-"):
            errors.append(f"{label}.id: functional requirements use FR-NNN IDs")
        elif isinstance(req_id, str) and kind == "non_functional" and not req_id.startswith("NFR-"):
            errors.append(f"{label}.id: non-functional requirements use NFR-NNN IDs")
        pattern = item.get("ears_pattern")
        if kind == "functional":
            if pattern not in PATTERNS:
                errors.append(f"{label}.ears_pattern: expected one of {', '.join(sorted(PATTERNS))}")
        elif kind == "non_functional" and pattern is not None:
            errors.append(f"{label}.ears_pattern: non-functional requirements use a measurable target, not an EARS pattern")

        statement = item.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            errors.append(f"{label}.statement: expected non-empty text")
        elif kind == "functional" and pattern in PATTERNS and not EARS_FORMS[pattern].fullmatch(statement.strip()):
            errors.append(f"{label}.statement: does not match the declared EARS pattern; syntax checks do not assess meaning")
        source = item.get("source")
        if not isinstance(source, str) or not source.strip():
            errors.append(f"{label}.source: expected non-empty provenance")

        criteria = item.get("acceptance_criteria")
        if not isinstance(criteria, list) or not criteria:
            errors.append(f"{label}.acceptance_criteria: expected at least one criterion")
            continue
        for criterion_index, criterion in enumerate(criteria):
            criterion_label = f"{label}.acceptance_criteria[{criterion_index}]"
            if not isinstance(criterion, dict):
                errors.append(f"{criterion_label}: expected mapping")
                continue
            ac_id = criterion.get("id")
            if not isinstance(ac_id, str) or not AC_ID_RE.fullmatch(ac_id):
                errors.append(f"{criterion_label}.id: expected AC-NNN")
            elif ac_id in acceptance_ids:
                errors.append(f"{criterion_label}.id: duplicate {ac_id}")
            else:
                acceptance_ids.add(ac_id)
            for field in ("observable_result", "verification_method"):
                value = criterion.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{criterion_label}.{field}: expected non-empty text")
            refs = criterion.get("evidence_refs", [])
            if not isinstance(refs, list) or not all(isinstance(ref, str) and ref.strip() for ref in refs):
                errors.append(f"{criterion_label}.evidence_refs: expected a list of non-empty paths")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        document = yaml.safe_load(args.registry.read_text(encoding="utf-8"))
        errors = validate(document)
    except (OSError, yaml.YAMLError) as exc:
        errors = [str(exc)]
    report = {"status": "PASS" if not errors else "FAIL", "errors": errors}
    if args.format == "json":
        print(json.dumps(report, sort_keys=True))
    elif errors:
        print("\n".join(errors))
    else:
        print("PASS")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
