"""Shared repository-relative path formatting."""

from __future__ import annotations

from pathlib import Path


def relative_path(root: Path, path: Path) -> str:
    """Return a POSIX repository-relative path or the resolved outside path."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())
