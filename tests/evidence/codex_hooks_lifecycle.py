from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / "harness/adapters/codex/hooks/pre_tool_use_policy.py"
PROBE = "printf 'AIPS_PLAN19_HOOK_PROBE'"


def invoke(payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


def main() -> int:
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": PROBE},
    }
    denied = invoke(json.dumps(event))
    assert denied.returncode == 0, denied.stderr
    output = json.loads(denied.stdout)
    specific = output["hookSpecificOutput"]
    assert specific["hookEventName"] == "PreToolUse"
    assert specific["permissionDecision"] == "deny"

    ordinary = invoke(json.dumps({**event, "tool_input": {"command": "pwd"}}))
    assert ordinary.returncode == 0 and ordinary.stdout == ""
    unsupported = invoke(json.dumps({**event, "tool_name": "WebSearch"}))
    assert unsupported.returncode == 0 and unsupported.stdout == ""
    malformed = invoke("{")
    assert malformed.returncode == 0 and malformed.stdout == ""

    config = json.loads((ROOT / "harness/adapters/codex/hooks/hooks.json").read_text(encoding="utf-8"))
    handler = config["hooks"]["PreToolUse"][0]["hooks"][0]
    assert handler["timeout"] == 3
    print("codex hook callback contract: PASS (synthetic event only; live runtime dispatch unverified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
