"""Resolve disposable caches without changing explicit configuration or permissions."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Mapping


def fallback_home() -> Path:
    return Path(tempfile.gettempdir()) / f"aips-runtime-cache-{os.getuid()}"


def trusted_fallback(path: Path) -> bool:
    if path.is_symlink():
        raise PermissionError("temporary AIPS cache must not be a symlink")
    if path.exists():
        info = path.stat()
        if not path.is_dir() or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise PermissionError("temporary AIPS cache must be a private directory owned by this user")
        return True
    return False


def writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=path, prefix=".aips-write-probe-"):
            pass
        return True
    except OSError:
        return False


def private_fallback() -> Path:
    path = fallback_home()
    trusted_fallback(path)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    trusted_fallback(path)
    return path


def cache_home(env: Mapping[str, str] | None = None, *, for_write: bool = False, namespace: str = "aips") -> Path:
    values = os.environ if env is None else env
    if values.get("XDG_CACHE_HOME"):
        return Path(values["XDG_CACHE_HOME"])
    default = Path(values.get("HOME") or Path.home()) / ".cache"
    fallback = fallback_home()
    if trusted_fallback(fallback):
        return fallback
    if not for_write or writable(default / namespace):
        return default
    return private_fallback()


def cache_environment(env: Mapping[str, str] | None = None) -> dict[str, str]:
    result = dict(os.environ if env is None else env)
    result["XDG_CACHE_HOME"] = str(cache_home(result, for_write=True, namespace="gh"))
    return result
