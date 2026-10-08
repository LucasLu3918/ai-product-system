"""Read the bounded, privacy-limited OpenCode AIPS execution trace."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

ALLOWED_FIELDS = {
    "at", "runtime", "event", "status", "decision", "level", "session", "project",
    "domain", "intent", "effect", "readiness", "workflow_count", "duration_ms",
    "context_bytes", "context_command_ms", "creative_asset_count", "truncated", "action", "reason_code", "project_mode",
    "session_root_source",
    "provider", "operation",
}
ENUMS = {
    "event": {"plugin", "context", "permission", "shell", "creative_execution"},
    "status": {"ready", "entered", "delivered", "unavailable"},
    "decision": {"ALLOW", "DENY", "UNSUPPORTED", "BLOCKED"},
    "level": {"L0", "L1", "L2", "L3"},
    "domain": {"creative", "software", "data", "document", "general", "unknown"},
    "intent": {"plan", "publish", "delete", "modify", "create", "read", "discuss", "unknown"},
    "effect": {"chat_only", "filesystem_write", "external_action", "unknown"},
    "readiness": {"READY", "PARTIAL", "UNREVIEWED", "unknown"},
    "project_mode": {"EPHEMERAL", "ATTACHED", "UNKNOWN"},
    "action": {"edit", "write", "patch", "apply_patch"},
    "reason_code": {"policy_allow", "policy_deny", "target_missing", "target_escape", "creative_target_exists", "creative_target_unsupported", "creative_git_workspace", "intelligence_not_ready", "intelligence_stale", "instruction_conflict", "action_unsupported", "external_approval_required", "session_directory_unavailable", "read_only_scan_failed", "shell_readonly_allow", "shell_aips_readonly", "shell_aips_command_unsupported", "shell_aips_arguments_unsupported", "shell_path_escape", "shell_operators_unsupported", "shell_command_unsupported", "shell_find_effect_unsupported", "shell_sed_effect_unsupported", "shell_git_command_unsupported", "shell_option_unsupported", "shell_policy_denied", "creative_ephemeral_required", "creative_bundle_invalid", "creative_timeout", "creative_execution_failed", "creative_response_invalid", "creative_tool_result"},
    "session_root_source": {"directory", "location_directory", "worktree"},
    "provider": {"mflux_local", "comfyui_local", "unknown"},
    "operation": {"generate", "edit", "unknown"},
}
HEX_IDS = re.compile(r"[0-9a-f]{16}")


def _clean(record: dict[str, Any]) -> dict[str, Any] | None:
    if set(record) - ALLOWED_FIELDS or record.get("runtime") != "opencode" or record.get("event") not in ENUMS["event"]:
        return None
    result: dict[str, Any] = {"runtime": "opencode", "event": record["event"]}
    for key, allowed in ENUMS.items():
        value = record.get(key)
        if value is not None:
            if value not in allowed:
                return None
            result[key] = value
    for key in ("session", "project"):
        value = record.get(key)
        if value is not None:
            if not isinstance(value, str) or not HEX_IDS.fullmatch(value):
                return None
            result[key] = value
    for key, maximum in (("workflow_count", 100), ("duration_ms", 600000), ("context_command_ms", 600000), ("context_bytes", 12000), ("creative_asset_count", 500)):
        value = record.get(key)
        if value is not None:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= maximum:
                return None
            result[key] = value
    for key in ("truncated",):
        value = record.get(key)
        if value is not None:
            if not isinstance(value, bool):
                return None
            result[key] = value
    timestamp = record.get("at")
    if timestamp is not None:
        if not isinstance(timestamp, str) or len(timestamp) > 32:
            return None
        result["at"] = timestamp
    return result


def trace_file() -> Path:
    state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")).expanduser()
    return state / "aips/opencode/events.jsonl"


def read_events(path: Path, limit: int = 20) -> dict[str, Any]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    if not path.exists():
        return {"status": "NO_EVENTS", "path": str(path), "events": []}
    events = []
    invalid = 0
    # Only inspect a bounded tail. Corrupt records are omitted, never echoed.
    lines = path.read_bytes()[-512 * 1024 :].splitlines()[-1000:]
    for line in lines:
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                invalid += 1
                continue
            clean = _clean(record)
            if clean is None:
                invalid += 1
                continue
            events.append(clean)
        except (json.JSONDecodeError, UnicodeDecodeError):
            invalid += 1
    return {"status": "READY" if events else "NO_EVENTS", "path": str(path), "invalid_records": invalid, "events": events[-limit:]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--file", type=Path, default=trace_file(), help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        print(json.dumps(read_events(args.file, args.limit), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "UNAVAILABLE", "reason": type(exc).__name__}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
