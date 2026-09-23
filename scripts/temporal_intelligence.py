#!/usr/bin/env python3
"""Deterministic, revision-aware temporal Project Intelligence helpers."""
from __future__ import annotations

import datetime as dt
import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml


UNKNOWN = "UNKNOWN"
QUALITY_VALUES = {"VERIFIED", "INFERRED", "PARTIAL", UNKNOWN}


def load_temporal(store: Path) -> dict[str, Any]:
    path = store / "TEMPORAL_ASSERTIONS.yaml"
    if not path.is_file():
        return {"schema": {"version": 1}, "assertions": [], "semantics": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("TEMPORAL_ASSERTIONS.yaml must contain a mapping")
    return data


def _git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )


def head_revision(root: Path) -> str:
    result = _git(root, ["rev-parse", "HEAD"])
    if result.returncode != 0:
        raise ValueError("unable to resolve repository HEAD")
    return result.stdout.strip()


def resolve_revision(root: Path, revision: str | None) -> str:
    candidate = (revision or "HEAD").strip()
    result = _git(root, ["rev-parse", "--verify", f"{candidate}^{{commit}}"])
    if result.returncode != 0:
        raise ValueError(f"unknown Git revision: {candidate}")
    return result.stdout.strip()


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    if ancestor == descendant:
        return True
    result = _git(root, ["merge-base", "--is-ancestor", ancestor, descendant])
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise ValueError(f"unable to compare Git revisions: {ancestor} -> {descendant}")


def _revision(value: Any) -> str | None:
    if value is None or str(value).strip().upper() == UNKNOWN:
        return None
    return str(value).strip()


def validate_document(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    schema = doc.get("schema") or {}
    if schema.get("version") not in (1, "1"):
        errors.append("schema.version must be 1")
    assertions = doc.get("assertions")
    if not isinstance(assertions, list):
        return ["assertions must be a list"]
    ids: set[str] = set()
    for index, assertion in enumerate(assertions):
        path = f"assertions[{index}]"
        if not isinstance(assertion, dict):
            errors.append(f"{path} must be a mapping")
            continue
        assertion_id = str(assertion.get("id") or "").strip()
        if not assertion_id:
            errors.append(f"{path}.id is required")
        elif assertion_id in ids:
            errors.append(f"duplicate assertion id: {assertion_id}")
        ids.add(assertion_id)
        for field in ("subject", "predicate", "object"):
            if not str(assertion.get(field) or "").strip():
                errors.append(f"{path}.{field} is required")
        validity = assertion.get("validity") or {}
        if not isinstance(validity, dict):
            errors.append(f"{path}.validity must be a mapping")
        else:
            if "from_revision" not in validity:
                errors.append(f"{path}.validity.from_revision is required; use UNKNOWN when unproven")
            if "to_revision_exclusive" not in validity:
                errors.append(f"{path}.validity.to_revision_exclusive is required; use null when open")
            start = _revision(validity.get("from_revision"))
            end = _revision(validity.get("to_revision_exclusive"))
            if start and end and start == end:
                errors.append(f"{path}.validity interval must be non-empty")
        quality = str(assertion.get("history_quality") or UNKNOWN).upper()
        if quality not in QUALITY_VALUES:
            errors.append(f"{path}.history_quality must be one of {sorted(QUALITY_VALUES)}")
        provenance = assertion.get("provenance")
        if provenance is not None and not isinstance(provenance, dict):
            errors.append(f"{path}.provenance must be a mapping")
    for assertion in assertions:
        if not isinstance(assertion, dict):
            continue
        target = assertion.get("supersedes") or []
        if isinstance(target, str):
            target = [target]
        if not isinstance(target, list):
            errors.append(f"{assertion.get('id')}.supersedes must be a list")
        for target_id in target:
            if str(target_id) not in ids:
                errors.append(f"{assertion.get('id')} supersedes unknown assertion: {target_id}")
        reverse = assertion.get("superseded_by")
        reverse_id = reverse.get("assertion") if isinstance(reverse, dict) else reverse
        if reverse_id and str(reverse_id) not in ids:
            errors.append(f"{assertion.get('id')} superseded_by unknown assertion: {reverse_id}")
    return errors


def _active(root: Path, assertion: dict[str, Any], target: str, explicit: bool) -> tuple[bool, str | None]:
    validity = assertion.get("validity") or {}
    start = _revision(validity.get("from_revision"))
    end = _revision(validity.get("to_revision_exclusive"))
    if start is None:
        if explicit:
            return False, "history_start_unknown"
        if end and is_ancestor(root, end, target):
            return False, None
        return True, "history_start_unknown"
    if not is_ancestor(root, start, target):
        return False, None
    if end and is_ancestor(root, end, target):
        return False, None
    return True, None


def active_assertions(root: Path, doc: dict[str, Any], revision: str | None = None) -> dict[str, Any]:
    errors = validate_document(doc)
    if errors:
        raise ValueError("invalid temporal assertions: " + "; ".join(errors))
    explicit = revision is not None
    target = resolve_revision(root, revision)
    active: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for assertion in doc.get("assertions") or []:
        ok, reason = _active(root, assertion, target, explicit)
        if ok:
            active.append(dict(assertion))
        elif reason:
            excluded.append({"id": assertion.get("id"), "reason": reason})
    return {
        "revision": target,
        "mode": "AS_OF" if explicit else "CURRENT",
        "assertions": active,
        "excluded": excluded,
        "conflicts": conflicts(active),
    }


def conflicts(assertions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for assertion in assertions:
        key = (str(assertion.get("subject")), str(assertion.get("predicate")))
        grouped.setdefault(key, []).append(assertion)
    result: list[dict[str, Any]] = []
    for (subject, predicate), values in grouped.items():
        objects = sorted({str(item.get("object")) for item in values})
        if len(objects) > 1:
            result.append({"subject": subject, "predicate": predicate, "objects": objects,
                           "assertions": [item.get("id") for item in values]})
    return result


def between(root: Path, doc: dict[str, Any], base: str, head: str) -> dict[str, Any]:
    base_doc = active_assertions(root, doc, base)
    head_doc = active_assertions(root, doc, head)
    base_ids = {str(item.get("id")) for item in base_doc["assertions"]}
    head_ids = {str(item.get("id")) for item in head_doc["assertions"]}
    return {
        "mode": "BETWEEN",
        "base": base_doc["revision"],
        "head": head_doc["revision"],
        "added": [item for item in head_doc["assertions"] if str(item.get("id")) not in base_ids],
        "ended": [item for item in base_doc["assertions"] if str(item.get("id")) not in head_ids],
        "superseded": [item for item in head_doc["assertions"] if item.get("supersedes")],
        "conflicts": head_doc["conflicts"],
    }


def why(doc: dict[str, Any], assertion_id: str) -> dict[str, Any]:
    errors = validate_document(doc)
    if errors:
        raise ValueError("invalid temporal assertions: " + "; ".join(errors))
    values = {str(item.get("id")): item for item in doc.get("assertions") or []}
    current = values.get(assertion_id)
    if not current:
        raise ValueError(f"unknown assertion: {assertion_id}")
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    cursor: dict[str, Any] | None = current
    while cursor and str(cursor.get("id")) not in seen:
        seen.add(str(cursor.get("id")))
        chain.append(cursor)
        reverse = cursor.get("superseded_by")
        next_id = reverse.get("assertion") if isinstance(reverse, dict) else reverse
        cursor = values.get(str(next_id)) if next_id else None
    return {"mode": "WHY", "assertion": current, "supersession_chain": chain}


def temporal_digest(doc: dict[str, Any]) -> str:
    payload = yaml.safe_dump(doc, sort_keys=True, allow_unicode=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def observed_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
