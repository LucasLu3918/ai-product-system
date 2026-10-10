"""Privacy-filtered bounded local creative execution trace persistence."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from performance_evidence import observed_distribution

MAX_RETRIES = 2

MAX_TIMEOUT_SECONDS = 3600

TRACE_LIMIT_BYTES = 512 * 1024

def trace_path() -> Path:
    state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")).expanduser()
    return state / "aips/creative-execution/events.jsonl"

def read_trace(limit: int = 20) -> dict[str, Any]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    path = trace_path()
    if not path.exists():
        return {"status": "NO_EVENTS", "events": [], "invalid_records": 0}
    allowed = {"at", "provider", "operation", "status", "reason_code", "attempts", "elapsed_ms", "input_sha256", "output_sha256"}
    events: list[dict[str, Any]] = []
    invalid = 0
    for line in path.read_bytes()[-TRACE_LIMIT_BYTES:].splitlines()[-500:]:
        try:
            item = json.loads(line)
            if not isinstance(item, dict) or set(item) - allowed:
                invalid += 1
                continue
            if item.get("provider") not in {"mflux_local", "comfyui_local"} or item.get("operation") not in {"generate", "edit"} or item.get("status") not in {"COMPLETE", "BLOCKED"}:
                invalid += 1
                continue
            if not isinstance(item.get("reason_code"), str) or len(item["reason_code"]) > 80 or not isinstance(item.get("at"), str) or len(item["at"]) > 40:
                invalid += 1
                continue
            if not isinstance(item.get("attempts"), int) or isinstance(item["attempts"], bool) or not 0 <= item["attempts"] <= MAX_RETRIES + 1:
                invalid += 1
                continue
            if not isinstance(item.get("elapsed_ms"), int) or isinstance(item["elapsed_ms"], bool) or not 0 <= item["elapsed_ms"] <= MAX_TIMEOUT_SECONDS * 1000:
                invalid += 1
                continue
            for key in ("input_sha256", "output_sha256"):
                value = item.get(key)
                if value is not None and (not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:") or any(char not in "0123456789abcdef" for char in value[7:])):
                    raise ValueError("invalid digest")
            events.append(item)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            invalid += 1
    return {"status": "READY" if events else "NO_EVENTS", "invalid_records": invalid, "events": events[-limit:],
            "observed_metrics": {
                "scope": "bounded_retained_events", "sample_count": len(events),
                "complete": sum(event["status"] == "COMPLETE" for event in events),
                "blocked": sum(event["status"] == "BLOCKED" for event in events),
                "elapsed_ms": observed_distribution([event.get("elapsed_ms") for event in events]),
                "human_visual_quality": "UNVERIFIED", "user_acceptance": "NOT_RECORDED",
            }}

def record_trace(event: dict[str, Any]) -> None:
    allowed = {"at", "provider", "operation", "status", "reason_code", "attempts", "elapsed_ms", "input_sha256", "output_sha256"}
    if set(event) - allowed:
        return
    try:
        path = trace_path()
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path.parent, 0o700)
        if path.exists() and path.stat().st_size > TRACE_LIMIT_BYTES:
            path.write_text("", encoding="utf-8")
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        os.chmod(path, 0o600)
    except OSError:
        pass
