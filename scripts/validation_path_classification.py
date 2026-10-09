"""Shared fail-closed repository path inventory for validation planners."""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any


def is_known_path(path: str, inventory: dict[str, Any]) -> bool:
    """Return whether a safe repository-relative path belongs to a known root."""
    if not isinstance(path, str) or not path or "\\" in path or "\0" in path:
        return False
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        return False
    roots, prefixes = inventory.get("known_root_paths"), inventory.get("known_path_prefixes")
    if not isinstance(roots, list) or not isinstance(prefixes, list):
        return False
    return path in roots or any(path.startswith(prefix) for prefix in prefixes if isinstance(prefix, str) and prefix)


def unknown_paths(paths: list[str], inventory: dict[str, Any]) -> list[str]:
    """Preserve every malformed or unregistered path as an unknown."""
    return sorted({path for path in paths if not is_known_path(path, inventory)})
