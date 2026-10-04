"""Pure publication policy calculations shared by preflight callers."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

import yaml

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def matches(paths: list[str], patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for path in paths for pattern in patterns)


def resolve_change_class(explicit: str, labels: str) -> tuple[str, str | None]:
    label_set = {item.strip() for item in labels.split(",") if item.strip()}
    label_class = "core" if "aips:core-change" in label_set else "large" if "aips:large-change" in label_set else "standard"
    if explicit == "auto":
        return label_class, None
    warning = None if explicit == label_class or not labels else f"explicit {explicit} differs from labels ({label_class})"
    return explicit, warning


def pr_creation_plan(change_class: str) -> dict[str, Any]:
    label = {"core": "aips:core-change", "large": "aips:large-change"}.get(change_class)
    return {
        "required_label": label,
        "gh_create_args": ["gh", "pr", "create", *(["--label", label] if label else [])],
        "label_timing": "initial_create_request" if label else "not_required",
        "note": "Include the change-class label in the PR creation request when the route supports it. GitHub may still emit a separate labeled event; classification-label changes rerun the full Gate, while unrelated label events skip the Gate without cancelling active validation and require matching successful full Gate evidence.",
    }


def matrix_required(profile: dict[str, Any], files: list[str], change_class: str) -> bool:
    if change_class in (profile.get("matrix_required_change_classes") or []):
        return True
    return matches(files, [str(item) for item in profile.get("matrix_required_paths") or []])


def documentation_impact(files: list[str], root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    sync = yaml.safe_load((root / "config/documentation-sync.yaml").read_text(encoding="utf-8")) or {}
    placement = yaml.safe_load((root / "config/documentation-placement.yaml").read_text(encoding="utf-8")) or {}
    closure = set(files)
    triggered: dict[str, dict[str, Any]] = {}
    required_by: dict[str, set[str]] = {}
    placement_hits = []
    for rule in placement.get("placement_rules") or []:
        patterns = [str(item) for item in rule.get("triggers") or []]
        if not matches(files, patterns):
            continue
        placements = rule.get("placements") or {}
        placement_hits.append({"id": rule.get("id"), "placements": placements})
        for path in placements:
            target = str(path)
            required_by.setdefault(target, set()).add(f"placement:{rule.get('id')}")
            closure.add(target)
    changed = True
    while changed:
        changed = False
        current = sorted(closure)
        technology = sync.get("technology_guide") or {}
        if matches(current, [str(item) for item in technology.get("triggers") or []]):
            target = str(technology.get("path") or "")
            if target:
                required_by.setdefault(target, set()).add("technology-guide")
                if target not in closure:
                    closure.add(target)
                    changed = True
        for rule in sync.get("rules") or []:
            patterns = [str(item) for item in rule.get("triggers") or []]
            if not matches(current, patterns):
                continue
            required = [str(item) for item in (rule.get("human_docs") or []) + (rule.get("agent_docs") or [])]
            triggered.setdefault(str(rule.get("id")), {"required": required})
            for path in required:
                required_by.setdefault(path, set()).add(f"sync:{rule.get('id')}")
            before = len(closure)
            closure.update(required)
            changed = changed or len(closure) != before
    required = sorted(closure - set(files))
    return {
        "changed_files": files,
        "triggered_rules": triggered,
        "required_additions": required,
        "required_by": {path: sorted(required_by.get(path, set())) for path in required},
        "complete": not required,
        "placement_rules": placement_hits,
    }
