#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "scripts" / "governance_guard.py"


def run(runtime: str, payload: dict) -> dict:
    result = subprocess.run([sys.executable, str(GUARD), "hook", "--runtime", runtime],
                            input=json.dumps(payload), capture_output=True, text=True,
                            env={**os.environ, "AIPS_RESOURCE_AUTHORIZATION_PROFILE": ""}, timeout=10)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


def main() -> int:
    claude = run("claude-code", {"tool_name": "Bash", "tool_input": {"command": "curl https://example.com"}, "cwd": str(ROOT)})
    if claude.get("hookSpecificOutput", {}).get("permissionDecision") != "deny":
        raise AssertionError(f"Claude pre-tool hook did not block unclassified external action: {claude}")
    gemini = run("gemini-cli", {"tool_name": "run_shell_command", "tool_input": {"command": "wget https://example.com"}, "cwd": str(ROOT)})
    if gemini.get("decision") != "deny":
        raise AssertionError(f"Gemini BeforeTool hook did not block unclassified external action: {gemini}")
    ordinary = run("gemini-cli", {"tool_name": "run_shell_command", "tool_input": {"command": "echo safe"}, "cwd": str(ROOT)})
    if ordinary != {}:
        raise AssertionError(f"unrelated tool call should preserve the existing pass-through: {ordinary}")
    print("runtime_policy native hook lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
