"""Serialize all writers of a run's append-only event stream."""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
from typing import Any


def append_event(path: Path, event: dict[str, Any], *, max_bytes: int | None = None) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(lock_fd, "r+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            sequence = 1
            if path.exists():
                with path.open("rb") as existing:
                    sequence += sum(bool(line.strip()) for line in existing)
            event["sequence"] = sequence
            encoded = (json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            if max_bytes is not None and len(encoded) > max_bytes:
                raise ValueError("event exceeds the bounded event size")
            fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
            with os.fdopen(fd, "ab") as output:
                output.write(encoded)
                output.flush()
                os.fsync(output.fileno())
            return sequence
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
