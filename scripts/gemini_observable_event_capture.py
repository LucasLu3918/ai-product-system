#!/usr/bin/env python3
"""Opt-in Gemini CLI AfterTool metadata capture for bounded AIPS evidence."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import yaml


class CaptureError(ValueError):
    pass


ALLOW_OUTPUT = {"decision": "allow", "suppressOutput": True}
TRUE_VALUES = {"1", "true", "yes", "on"}


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise CaptureError(f"{path}: expected mapping")
    return value


def validate_config(config: dict[str, Any]) -> None:
    if config.get("version") != 1:
        raise CaptureError("config.version must be 1")
    if config.get("runtime") != "gemini-cli" or config.get("hook_event") != "AfterTool":
        raise CaptureError("capture config must remain Gemini CLI AfterTool")
    if config.get("enabled_by_default") is not False:
        raise CaptureError("capture must remain disabled by default")
    if config.get("sink_policy") != "explicit_temp_file_only":
        raise CaptureError("sink policy must remain explicit_temp_file_only")
    if not isinstance(config.get("max_sink_bytes"), int) or config["max_sink_bytes"] < 1024:
        raise CaptureError("max_sink_bytes must be a bounded positive integer")
    tools = config.get("supported_tools")
    if not isinstance(tools, dict) or set(tools) != {"read_file", "write_file", "replace"}:
        raise CaptureError("v1 capture scope must remain read_file/write_file/replace")
    for tool_name, mapping in tools.items():
        if not isinstance(mapping, dict):
            raise CaptureError(f"{tool_name}: mapping must be a mapping")
        if mapping.get("operation") not in {"read", "update"}:
            raise CaptureError(f"{tool_name}: unsupported operation")
        if mapping.get("network_used") is not False:
            raise CaptureError(f"{tool_name}: v1 file-tool capture must remain network_used=false")
        if not str(mapping.get("resource_id") or "").strip():
            raise CaptureError(f"{tool_name}: resource_id is required")
    verification = config.get("verification") or {}
    live_runtime = verification.get("live_runtime_execution_verified")
    live_capture = verification.get("live_capture_verified")
    if not isinstance(live_runtime, bool) or not isinstance(live_capture, bool):
        raise CaptureError("runtime/capture verification flags must be boolean")
    if live_capture and not live_runtime:
        raise CaptureError("live_capture_verified requires live_runtime_execution_verified")
    if live_runtime:
        if verification.get("verification_method") != "exact_candidate_installed_cli_fake_responses":
            raise CaptureError("verified live runtime requires exact-candidate installed CLI evidence")
        if verification.get("gemini_cli_version") != "0.60.0":
            raise CaptureError("verified Gemini CLI version must remain pinned to 0.60.0")
        if verification.get("provider_model_api_exercised") is not False:
            raise CaptureError("runtime verification must not claim provider API execution")
        if verification.get("provider_model_execution_verified") is not False:
            raise CaptureError("runtime verification must keep provider-model verification false")
    enforcement = config.get("enforcement") or {}
    for key in ("runtime_enforced", "critical_path", "automatic_remediation"):
        if enforcement.get(key) is not False:
            raise CaptureError(f"enforcement.{key} must remain false")
    authority = config.get("authority") or {}
    if any(value is not False for value in authority.values()):
        raise CaptureError("capture config must grant no protected authority")


def enabled(config: dict[str, Any], environ: dict[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    raw = str(env.get(str(config["enable_env"]), "")).strip().lower()
    return raw in TRUE_VALUES if raw else bool(config.get("enabled_by_default", False))


def _iso8601(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CaptureError("timestamp is required")
    cleaned = value.strip()
    try:
        datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CaptureError("timestamp must be ISO-8601") from exc
    return cleaned


def build_event(payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        raise CaptureError("hook input must be a JSON object")
    if payload.get("hook_event_name") != "AfterTool":
        raise CaptureError("hook_event_name must be AfterTool")
    tool_name = str(payload.get("tool_name") or "").strip()
    mapping = (config.get("supported_tools") or {}).get(tool_name)
    if mapping is None:
        return None
    response = payload.get("tool_response")
    if not isinstance(response, dict):
        raise CaptureError("tool_response must be a mapping")
    timestamp = _iso8601(payload.get("timestamp"))
    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        raise CaptureError("session_id is required")

    event_seed = f"{session_id}|{timestamp}|{tool_name}"
    event_id = "gemini-" + hashlib.sha256(event_seed.encode("utf-8")).hexdigest()[:24]
    outcome = "FAILED" if bool(response.get("error")) else "SUCCESS"

    return {
        "event_id": event_id,
        "observed_at": timestamp,
        "runtime": "gemini-cli",
        "adapter_id": str(config["adapter_id"]),
        "subject": str(config["subject"]),
        "resource_id": str(mapping["resource_id"]),
        "operation": str(mapping["operation"]),
        "observed_outcome": outcome,
        "network_used": False,
    }


def _resolve_sink(path_text: str) -> Path:
    if not path_text.strip():
        raise CaptureError("enabled capture requires an explicit ephemeral sink path")
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        raise CaptureError("capture sink must be absolute")
    resolved = path.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    try:
        resolved.relative_to(temp_root)
    except ValueError as exc:
        raise CaptureError("capture sink must stay under the system temporary directory") from exc
    return resolved


def persist_event(event: dict[str, Any], sink_text: str, max_bytes: int) -> None:
    sink = _resolve_sink(sink_text)
    sink.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    size = sink.stat().st_size if sink.exists() else 0
    if size + len(rendered.encode("utf-8")) > max_bytes:
        raise CaptureError("bounded ephemeral sink is full")
    fd = os.open(sink, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, rendered.encode("utf-8"))
    finally:
        os.close(fd)


def process_payload(
    payload: dict[str, Any],
    config: dict[str, Any],
    *,
    capture_enabled: bool,
    sink_text: str,
) -> dict[str, Any]:
    validate_config(config)
    if not capture_enabled:
        return {"status": "DISABLED", "captured": False}
    try:
        event = build_event(payload, config)
        if event is None:
            return {"status": "SKIPPED_UNSUPPORTED", "captured": False}
        persist_event(event, sink_text, int(config["max_sink_bytes"]))
        return {"status": "CAPTURED", "captured": True, "event": event}
    except CaptureError as exc:
        return {"status": "DEGRADED", "captured": False, "reason": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    hook = sub.add_parser("hook")
    hook.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()

    config = load_yaml(args.config)
    validate_config(config)
    try:
        payload = json.load(__import__("sys").stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps(ALLOW_OUTPUT, separators=(",", ":")))
        print(f"AIPS observable-event capture degraded: invalid JSON: {exc}", file=__import__("sys").stderr)
        return 0

    env = os.environ
    result = process_payload(
        payload,
        config,
        capture_enabled=enabled(config, env),
        sink_text=str(env.get(str(config["sink_env"]), "")),
    )
    if result["status"] == "DEGRADED":
        print(f"AIPS observable-event capture degraded: {result.get('reason', 'unknown')}", file=__import__("sys").stderr)
    print(json.dumps(ALLOW_OUTPUT, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
