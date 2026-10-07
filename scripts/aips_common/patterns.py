"""Glob matching primitives with explicit caller-specific compatibility modes."""

from __future__ import annotations

import fnmatch
from typing import Literal

PathMode = Literal["raw", "slash", "slash_prefix", "slash_lstrip"]


def _normalize(value: str, mode: PathMode) -> str:
    if mode == "raw":
        return value
    normalized = value.replace("\\", "/")
    if mode == "slash_prefix" and normalized.startswith("./"):
        return normalized[2:]
    if mode == "slash_lstrip":
        return normalized.lstrip("./")
    return normalized


def glob_matches(
    path: str,
    pattern: str,
    *,
    path_mode: PathMode = "raw",
    pattern_mode: PathMode = "raw",
    globstar_zero_directory: bool = False,
    globstar_as_star: bool = False,
    directory_suffix: bool = False,
    case_sensitive: bool = False,
) -> bool:
    """Match a path while making legacy normalization and globstar rules explicit."""
    normalized_path = _normalize(path, path_mode)
    normalized_pattern = _normalize(pattern, pattern_mode)
    matcher = fnmatch.fnmatchcase if case_sensitive else fnmatch.fnmatch
    if matcher(normalized_path, normalized_pattern):
        return True
    if globstar_zero_directory and normalized_pattern.startswith("**/") and matcher(normalized_path, normalized_pattern[3:]):
        return True
    if globstar_as_star:
        alternate = normalized_pattern.replace("**/", "*")
        if matcher(normalized_path, alternate):
            return True
    if directory_suffix and normalized_pattern.endswith("/**"):
        prefix = normalized_pattern[:-3].rstrip("/") + "/"
        if normalized_path.startswith(prefix):
            return True
    return False
