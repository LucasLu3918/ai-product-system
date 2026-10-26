"""Garbage collection for orphaned external Project Intelligence stores.

Only ``<config_home>/projects/<workspace>/intelligence`` directories are
considered. A store is an orphan only when its recorded project root is an
absolute path and nothing exists at that path. Dry-run is the default; removal
requires an explicit ``apply=True`` (``aips intelligence gc --yes``).
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import yaml

STORE_NAME = "intelligence"
MANIFEST_NAME = "PROJECT_INTELLIGENCE.yaml"


def _recorded_root(store: Path) -> tuple[str | None, str | None]:
    manifest = store / MANIFEST_NAME
    if manifest.is_symlink() or not manifest.is_file():
        return None, "manifest_missing"
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None, "manifest_unreadable"
    project = data.get("project") if isinstance(data, dict) else None
    root = project.get("root") if isinstance(project, dict) else None
    if not isinstance(root, str) or not root.strip():
        return None, "project_root_unrecorded"
    if not os.path.isabs(root):
        return None, "project_root_not_absolute"
    return root, None


def _path_present(path: str) -> bool | None:
    """Return True when anything (even a broken symlink) exists, None if unverifiable."""
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    except NotADirectoryError:
        return False
    except OSError:
        return None
    return True


def _confined(base: Path, entry: Path, store: Path) -> bool:
    try:
        resolved_entry = entry.resolve(strict=True)
        resolved_store = store.resolve(strict=True)
    except OSError:
        return False
    return resolved_entry.parent == base and resolved_store.parent == resolved_entry


def collect(projects_dir: Path, *, apply: bool = False) -> dict[str, Any]:
    """Classify external stores and remove orphans only when ``apply`` is True."""
    result: dict[str, Any] = {
        "mode": "APPLY" if apply else "DRY_RUN",
        "projects_dir": str(projects_dir),
        "orphaned": [],
        "kept": [],
        "skipped": [],
        "removed": [],
        "errors": [],
    }
    if projects_dir.is_symlink():
        result["status"] = "REFUSED"
        result["reason"] = "projects_dir_is_symlink"
        return result
    if not projects_dir.is_dir():
        result["status"] = "NO_STORES"
        return result
    base = projects_dir.resolve(strict=True)
    for entry in sorted(base.iterdir(), key=lambda item: item.name):
        store = entry / STORE_NAME
        record = {"workspace_id": entry.name, "store": str(store)}
        if entry.is_symlink():
            result["skipped"].append({**record, "reason": "workspace_is_symlink"})
            continue
        if not entry.is_dir():
            continue
        if store.is_symlink():
            result["skipped"].append({**record, "reason": "store_is_symlink"})
            continue
        if not store.is_dir():
            continue
        if not _confined(base, entry, store):
            result["skipped"].append({**record, "reason": "store_outside_projects_dir"})
            continue
        root, problem = _recorded_root(store)
        if root is None:
            result["skipped"].append({**record, "reason": problem})
            continue
        record["project_root"] = root
        present = _path_present(root)
        if present is None:
            result["skipped"].append({**record, "reason": "project_root_unverifiable"})
            continue
        if present:
            result["kept"].append({**record, "reason": "project_root_exists"})
            continue
        result["orphaned"].append({**record, "reason": "project_root_missing"})
        if not apply:
            continue
        # Re-check immediately before deletion; never delete a store whose
        # project path reappeared or whose confinement changed.
        if _path_present(root) is not False or not _confined(base, entry, store) or store.is_symlink():
            result["skipped"].append({**record, "reason": "changed_before_removal"})
            continue
        try:
            shutil.rmtree(store)
        except OSError as exc:
            result["errors"].append({**record, "reason": type(exc).__name__})
            continue
        result["removed"].append(record)
        try:
            entry.rmdir()
        except OSError:
            pass  # Other workspace data (runs, changes) is preserved.
    result["status"] = "APPLIED" if apply else "DRY_RUN"
    if not apply and result["orphaned"]:
        result["next"] = "Review the orphaned stores, then run: aips intelligence gc --yes"
    return result
