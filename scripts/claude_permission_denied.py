"""Observer-only, privacy-bounded Claude Code PermissionDenied hook."""
from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

VERSION = 1
MAX_RECORDS = 1000
MAX_AGE = dt.timedelta(days=30)
MAX_FILE_BYTES = 4 * 1024 * 1024
ALLOWED_TOOLS = {"Bash", "Edit", "Write", "NotebookEdit", "MultiEdit", "Read", "Task", "Other"}
RECORD_FIELDS = {
    "version", "timestamp", "event", "source", "reason_class", "tool_name",
    "reason_sha256", "tool_input_sha256", "tool_use_id_sha256", "session_id_sha256",
}


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.UTC)
    return value.astimezone(dt.UTC)


def _default_path() -> Path:
    home = Path.home().resolve(strict=True)
    return home / ".local" / "state" / "aips" / "diagnostics" / "claude-permission-denied.jsonl"


def _canonical_log_path(path: Path | None) -> Path:
    requested = path if path is not None else _default_path()
    directory = requested.parent
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    resolved_dir = directory.resolve(strict=True)
    # Resolve once, then reject symlinked components along the effective path.
    cursor = Path(resolved_dir.anchor)
    for component in resolved_dir.parts[1:]:
        cursor = cursor / component
        info = cursor.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise OSError("diagnostic directory path is not a real directory")
    os.chmod(resolved_dir, 0o700)
    if hasattr(os, "getuid") and resolved_dir.stat().st_uid != os.getuid():
        raise OSError("diagnostic directory owner is invalid")
    return resolved_dir / requested.name


def _read_records(path: Path, now: dt.datetime) -> list[dict[str, Any]]:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return []
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise OSError("diagnostic file is not a regular file")
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        raise OSError("diagnostic file owner is invalid")
    if info.st_size > MAX_FILE_BYTES:
        raise OSError("diagnostic file exceeds its size bound")
    os.chmod(path, 0o600)
    lines = path.read_text(encoding="utf-8").splitlines()
    kept: list[dict[str, Any]] = []
    for line in lines[-MAX_RECORDS:]:
        if len(line) > 8192:
            continue
        try:
            item = json.loads(line)
            timestamp = dt.datetime.fromisoformat(item["timestamp"])
            timestamp = _utc(timestamp)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            continue
        if set(item) != RECORD_FIELDS or item.get("event") != "PermissionDenied" or item.get("source") != "claude_auto_mode":
            continue
        if now - MAX_AGE <= timestamp <= now + dt.timedelta(minutes=5):
            kept.append(item)
    return kept


def record(payload: Any, *, path: Path | None = None, now: dt.datetime | None = None) -> bool:
    """Append a fixed-field redacted observation; all storage errors are non-blocking."""
    try:
        if not isinstance(payload, dict) or payload.get("hook_event_name") != "PermissionDenied":
            return False
        current = _utc(now or dt.datetime.now(dt.UTC))
        log_path = _canonical_log_path(path)
        lock_path = log_path.with_name(log_path.name + ".lock")
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            os.fchmod(lock_fd, 0o600)
            if hasattr(os, "getuid") and os.fstat(lock_fd).st_uid != os.getuid():
                return False
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            records = _read_records(log_path, current)
            tool_name = payload.get("tool_name")
            if not isinstance(tool_name, str) or tool_name not in ALLOWED_TOOLS:
                tool_name = "Other"
            reason = payload.get("reason")
            reason_text = reason if isinstance(reason, str) else ""
            record_value = {
                "version": VERSION,
                "timestamp": current.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "event": "PermissionDenied",
                "source": "claude_auto_mode",
                "reason_class": "self_modification" if re.search(r"self[ -]modification", reason_text, re.IGNORECASE) else "other",
                "tool_name": tool_name,
                "reason_sha256": _digest(reason_text),
                "tool_input_sha256": _digest(payload.get("tool_input")),
                "tool_use_id_sha256": _digest(payload.get("tool_use_id")),
                "session_id_sha256": _digest(payload.get("session_id")),
            }
            records.append(record_value)
            records = records[-MAX_RECORDS:]
            body = "".join(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n" for item in records)
            descriptor, temporary = tempfile.mkstemp(prefix=".claude-denied-", dir=log_path.parent)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    stream.write(body)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, 0o600)
                if log_path.is_symlink():
                    return False
                os.replace(temporary, log_path)
                os.chmod(log_path, 0o600)
            finally:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass
            return True
        finally:
            os.close(lock_fd)
    except Exception:  # noqa: BLE001 - storage must never affect Claude's refusal
        # This observer must never change the Host's PermissionDenied decision.
        return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 - malformed hook input is a silent no-op
        print("{}")
        return 0
    record(payload)
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
