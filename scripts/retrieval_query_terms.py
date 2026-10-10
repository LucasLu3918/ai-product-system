"""Bounded lexical query normalization and curated alias expansion."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

SEMANTIC_ALIAS_LIMIT = 32

SEMANTIC_ALIAS_PATH = Path(__file__).resolve().parents[1] / "templates/intelligence/SEMANTIC_ALIASES.yaml"

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}|[\u4e00-\u9fff]{2,}")

def query_terms(query: str) -> list[str]:
    result: list[str] = []
    for token in TOKEN_RE.findall(query):
        low = token.lower()
        if low not in result:
            result.append(low)
    return result[:20]

def semantic_alias_expansion(terms: list[str]) -> tuple[list[str], dict[str, Any]]:
    telemetry: dict[str, Any] = {
        "provider": "builtin-curated-software-aliases",
        "matched_groups": [],
        "matched_group_terms": {},
        "expanded_terms": [],
        "truncated": False,
        "limit": SEMANTIC_ALIAS_LIMIT,
    }
    if not SEMANTIC_ALIAS_PATH.is_file():
        telemetry["status"] = "UNAVAILABLE"
        return [], telemetry
    try:
        doc = yaml.safe_load(SEMANTIC_ALIAS_PATH.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError):
        telemetry["status"] = "INVALID"
        return [], telemetry

    source_terms = set(terms)
    expanded: list[str] = []
    for group in doc.get("groups") or []:
        if not isinstance(group, dict):
            continue
        group_terms = [
            str(item).lower()
            for item in (group.get("terms") or [])
            if str(item).strip()
        ]
        if not source_terms.intersection(group_terms):
            continue
        group_id = str(group.get("id") or "unnamed")
        telemetry["matched_groups"].append(group_id)
        telemetry["matched_group_terms"][group_id] = group_terms
        for term in group_terms:
            if term in source_terms or term in expanded:
                continue
            if len(expanded) >= SEMANTIC_ALIAS_LIMIT:
                telemetry["truncated"] = True
                break
            expanded.append(term)
        if telemetry["truncated"]:
            break
    telemetry["expanded_terms"] = expanded
    telemetry["status"] = "READY"
    return expanded, telemetry

def fts_expression(terms: list[str]) -> str:
    safe = [re.sub(r"[^A-Za-z0-9_\u4e00-\u9fff]", "", term) for term in terms]
    safe = [term for term in safe if term]
    return " OR ".join(f'"{term}"' for term in safe)
