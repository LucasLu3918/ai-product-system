#!/usr/bin/env python3
"""Disabled-by-default Codex PostToolUse observable-event capture Trial."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any

import yaml

import agent_anomaly_evaluation as anomaly

DEFAULT_CONFIG = {
    "version": 1,
    "enabled": False,
    "runtime": "codex",
    "adapter_id": "codex-post-tool-use-v1",
    "mode": "POST_EXECUTION_EVIDENCE",
    "max_events": 32,
    "max_string_length": 160,
    "lock_timeout_ms": 100,
    "hook_contract_verified": True,
    "hook_trust_verified": False,
    "live_capture_verified": False,
    "runtime_enforced": False,
    "critical_path": False,
    "automatic_remediation": False,
    "raw_payload_persisted": False,
}

HEALTH_DEFAULT = {
    "accepted": 0,
    "dropped_sensitive": 0,
    "dropped_unresolved_outcome": 0,
    "dropped_unsupported": 0,
    "dropped_buffer_full": 0,
    "duplicates": 0,
    "degraded_lock_timeout": 0,
    "last_status": None,
}


class CaptureError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def config_path_default() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "aips" / "harness" / "codex-observable-event-capture.yaml"


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return dict(DEFAULT_CONFIG)
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise CaptureError("capture config must be a mapping")
    config = dict(DEFAULT_CONFIG)
    config.update(value)
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    if config.get("version") != 1:
        raise CaptureError("config.version must be 1")
    if config.get("runtime") != "codex":
        raise CaptureError("runtime must be codex")
    if config.get("mode") != "POST_EXECUTION_EVIDENCE":
        raise CaptureError("mode must remain POST_EXECUTION_EVIDENCE")
    for key in ("max_events", "max_string_length", "lock_timeout_ms"):
        value = config.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise CaptureError(f"{key} must be a positive integer")
    for key in (
        "runtime_enforced",
        "critical_path",
        "automatic_remediation",
        "raw_payload_persisted",
        "live_capture_verified",
    ):
        if config.get(key) is not False:
            raise CaptureError(f"{key} must remain false in this Trial")


def _status_from_response(response: Any) -> str | None:
    if not isinstance(response, dict):
        return None
    if isinstance(response.get("is_error"), bool):
        return "FAILED" if response["is_error"] else "SUCCESS"
    if isinstance(response.get("success"), bool):
        return "SUCCESS" if response["success"] else "FAILED"
    for key in ("exit_code", "returncode"):
        value = response.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return "SUCCESS" if value == 0 else "FAILED"
    status = response.get("status")
    if isinstance(status, str):
        normalized = status.strip().lower()
        if normalized in {"success", "ok", "completed"}:
            return "SUCCESS"
        if normalized in {"failed", "error"}:
            return "FAILED"
    return None


def _bounded_string(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CaptureError(f"{field} must be a non-empty string")
    value = value.strip()
    if len(value) > maximum:
        raise CaptureError(f"{field} exceeds max_string_length")
    return value


def normalize_codex_post_tool(
    payload: dict[str, Any],
    config: dict[str, Any],
    *,
    observed_at: str | None = None,
    env: dict[str, str] | None = None,
) -> tuple[str, dict[str, Any] | None]:
    if payload.get("hook_event_name") != "PostToolUse":
        return "DROPPED_UNSUPPORTED", None
    if str(payload.get("tool_name") or "") != "apply_patch":
        return "DROPPED_UNSUPPORTED", None

    sensitive = {
        "tool_input": payload.get("tool_input"),
        "tool_response": payload.get("tool_response"),
    }
    if anomaly.forbidden_paths(sensitive) or anomaly.secret_findings(sensitive):
        return "DROPPED_SENSITIVE", None

    outcome = _status_from_response(payload.get("tool_response"))
    if outcome is None:
        return "DROPPED_UNRESOLVED_OUTCOME", None

    maximum = int(config["max_string_length"])
    tool_use_id = _bounded_string(payload.get("tool_use_id"), "tool_use_id", maximum)
    event_id = "codex-" + anomaly.digest(tool_use_id).split(":", 1)[1][:24]
    event: dict[str, Any] = {
        "event_id": event_id,
        "observed_at": observed_at or utc_now(),
        "runtime": "codex",
        "adapter_id": str(config["adapter_id"]),
        "subject": "codex-agent",
        "resource_id": "repository-patch",
        "operation": "update",
        "observed_outcome": outcome,
        "network_used": False,
    }

    boundary = (env or os.environ).get("AIPS_CHANGE_BOUNDARY")
    if boundary:
        boundary = _bounded_string(boundary, "change_boundary", maximum)
        if anomaly.secret_findings(boundary):
            return "DROPPED_SENSITIVE", None
        event["change_boundary"] = boundary

    return "ACCEPTED", event


@contextmanager
def spool_lock(spool: Path, timeout_ms: int):
    spool.mkdir(parents=True, exist_ok=True)
    lock = spool / ".capture.lock"
    deadline = time.monotonic() + timeout_ms / 1000.0
    fd: int | None = None
    while time.monotonic() < deadline:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            time.sleep(0.005)
    if fd is None:
        raise TimeoutError("capture spool lock timeout")
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)


def _health_path(spool: Path) -> Path:
    return spool / "health.json"


def _load_health(spool: Path) -> dict[str, Any]:
    path = _health_path(spool)
    if not path.exists():
        return dict(HEALTH_DEFAULT)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(HEALTH_DEFAULT)
    health = dict(HEALTH_DEFAULT)
    if isinstance(value, dict):
        health.update(value)
    return health


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    temp = path.with_name(path.name + f".tmp-{os.getpid()}")
    temp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _record_status(spool: Path, config: dict[str, Any], status: str, event: dict[str, Any] | None) -> dict[str, Any]:
    try:
        with spool_lock(spool, int(config["lock_timeout_ms"])):
            health = _load_health(spool)
            key = {
                "DROPPED_SENSITIVE": "dropped_sensitive",
                "DROPPED_UNRESOLVED_OUTCOME": "dropped_unresolved_outcome",
                "DROPPED_UNSUPPORTED": "dropped_unsupported",
            }.get(status)

            if status == "ACCEPTED" and event is not None:
                files = sorted(spool.glob("event-*.json"))
                if len(files) >= int(config["max_events"]):
                    status = "DROPPED_BUFFER_FULL"
                    health["dropped_buffer_full"] = int(health.get("dropped_buffer_full", 0)) + 1
                else:
                    target = spool / f"event-{event['event_id']}.json"
                    if target.exists():
                        status = "DUPLICATE"
                        health["duplicates"] = int(health.get("duplicates", 0)) + 1
                    else:
                        _write_json_atomic(target, event)
                        health["accepted"] = int(health.get("accepted", 0)) + 1
            elif key:
                health[key] = int(health.get(key, 0)) + 1

            health["last_status"] = status
            health["live_capture_verified"] = False
            health["raw_payload_persisted"] = False
            _write_json_atomic(_health_path(spool), health)
            return {
                "status": status,
                "event_fingerprint": anomaly.digest(event) if event is not None and status in {"ACCEPTED", "DUPLICATE"} else None,
            }
    except TimeoutError:
        return {"status": "DEGRADED_LOCK_TIMEOUT", "event_fingerprint": None}


def process_hook(
    payload: dict[str, Any],
    *,
    config_path: Path | None,
    spool: Path,
    observed_at: str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    if config.get("enabled") is not True:
        return {"status": "DISABLED", "event_fingerprint": None}
    status, event = normalize_codex_post_tool(payload, config, observed_at=observed_at, env=env)
    return _record_status(spool, config, status, event)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("hook",))
    parser.add_argument("--runtime", choices=("codex",), default="codex")
    parser.add_argument("--config", type=Path, default=config_path_default())
    parser.add_argument("--spool", type=Path, required=True)
    parser.add_argument("--diagnostic-json", action="store_true")
    args = parser.parse_args()

    result = {"status": "DEGRADED_ERROR", "event_fingerprint": None}
    try:
        payload = json.load(__import__("sys").stdin)
        if not isinstance(payload, dict):
            raise CaptureError("hook stdin must be a JSON object")
        result = process_hook(payload, config_path=args.config, spool=args.spool)
    except Exception:
        # Post-execution evidence must never become a tool-execution blocker.
        result = {"status": "DEGRADED_ERROR", "event_fingerprint": None}

    if args.diagnostic_json:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
