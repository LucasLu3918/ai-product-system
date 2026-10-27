"""Short-lived, non-authorizing evidence that an exact candidate passed Secret Scan."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import time
from pathlib import Path
from typing import Any

import runtime_cache

TTL_SECONDS = 1800
SCHEMA_VERSION = 1


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def binding(root: Path, scope: dict[str, Any], *, policy_digest: str) -> dict[str, str]:
    """Bind scan evidence to repository/worktree, exact candidate and push semantics."""
    scanner = Path(__file__).with_name("check_secret_leakage.py")
    scanner_digest = "sha256:" + hashlib.sha256(scanner.read_bytes()).hexdigest()
    return {
        "repository_id": str(scope["repository_id"]),
        "worktree_id": str(scope["worktree_id"]),
        "base_commit": str(scope["base_commit"]),
        "candidate_commit": str(scope["candidate_commit"]),
        "operation": str(scope["operations"][0]),
        "remote": str(scope["remote"]),
        "target_ref": str(scope["target_ref"]),
        "expected_remote_oid": str(scope.get("expected_remote_oid") or ""),
        "diff_digest": str(scope["diff_digest"]),
        "policy_digest": str(policy_digest),
        "scanner_digest": scanner_digest,
    }


def _cache_dir(*, create: bool) -> Path:
    base = runtime_cache.cache_home(for_write=create, namespace="aips")
    if base.is_symlink():
        raise OSError("cache root must not be a symlink")
    path = base / "aips-publication-scan-evidence"
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return path
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise OSError("scan evidence cache must be a real directory")
    if hasattr(os, "geteuid") and info.st_uid != os.geteuid():
        raise OSError("scan evidence cache has an unexpected owner")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise OSError("scan evidence cache must be private")
    return path


def store(root: Path, scope: dict[str, Any], *, policy_digest: str,
          now: float | None = None) -> str:
    """Atomically store a passing scan observation in the private user cache."""
    bound = binding(root, scope, policy_digest=policy_digest)
    issued = time.time() if now is None else now
    payload = {"version": SCHEMA_VERSION, "status": "PASS", "issued_at": issued,
               "expires_at": issued + TTL_SECONDS, "binding": bound}
    payload["integrity"] = _digest(payload)
    directory = _cache_dir(create=True)
    name = hashlib.sha256(_canonical(bound)).hexdigest() + ".json"
    fd, temporary = tempfile.mkstemp(prefix=".scan-evidence-", dir=directory)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(_canonical(payload))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, directory / name)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return "sha256:" + hashlib.sha256(_canonical(bound)).hexdigest()


def valid(root: Path, scope: dict[str, Any], *, policy_digest: str,
          now: float | None = None) -> bool:
    """Return true only for fresh, intact evidence matching every bound field."""
    try:
        bound = binding(root, scope, policy_digest=policy_digest)
        directory = _cache_dir(create=False)
        path = directory / (hashlib.sha256(_canonical(bound)).hexdigest() + ".json")
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
            return False
        if hasattr(os, "geteuid") and info.st_uid != os.geteuid():
            return False
        if stat.S_IMODE(info.st_mode) & 0o077:
            return False
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return False
        integrity = payload.pop("integrity", None)
        current = time.time() if now is None else now
        return bool(
            payload.get("version") == SCHEMA_VERSION
            and payload.get("status") == "PASS"
            and payload.get("binding") == bound
            and type(payload.get("issued_at")) in (int, float)
            and type(payload.get("expires_at")) in (int, float)
            and payload["issued_at"] <= current <= payload["expires_at"]
            and payload["expires_at"] - payload["issued_at"] <= TTL_SECONDS
            and isinstance(integrity, str)
            and integrity == _digest(payload)
        )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False
