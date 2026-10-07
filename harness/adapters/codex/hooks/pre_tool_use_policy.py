"""Deny one harmless synthetic Bash command to probe the Codex hook contract."""
from __future__ import annotations

import json
import sys
from typing import Any

PROBE_COMMAND = "printf 'AIPS_PLAN19_HOOK_PROBE'"


def decision(event: Any) -> dict[str, Any] | None:
    if not isinstance(event, dict) or event.get("hook_event_name") != "PreToolUse":
        return None
    if event.get("tool_name") != "Bash":
        return None
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict) or tool_input.get("command") != PROBE_COMMAND:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Plan19 synthetic hook probe denied the harmless test command.",
        }
    }


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Unknown input must not accidentally claim enforcement.
        return 0
    result = decision(event)
    if result is not None:
        sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
