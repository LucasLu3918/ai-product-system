#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "scripts" / "governance_guard.py"


def run(runtime: str, payload: dict, *, extra_env: dict[str, str] | None = None) -> dict:
    result = subprocess.run([sys.executable, str(GUARD), "hook", "--runtime", runtime],
                            input=json.dumps(payload), capture_output=True, text=True,
                            env={**os.environ, "AIPS_RESOURCE_AUTHORIZATION_PROFILE": "", **(extra_env or {})}, timeout=10)
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

    with tempfile.TemporaryDirectory() as tmp:
        profile_root = Path(tmp)
        missing_payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "curl https://analytics.example.com/v1/events"},
            "cwd": str(profile_root),
        }
        missing = run("claude-code", missing_payload,
                      extra_env={"AIPS_RESOURCE_AUTHORIZATION_PROFILE": "missing/profile.yaml"})
        reason = missing["hookSpecificOutput"]["permissionDecisionReason"]
        marker = "AIPS diagnostic="
        if marker not in reason:
            raise AssertionError(f"Claude denial omitted safe Profile resolution details: {missing}")
        details = json.loads(reason.split(marker, 1)[1])
        if details.get("profile_resolution", {}).get("path") != "missing/profile.yaml":
            raise AssertionError(f"Claude denial must show the project-relative Profile path: {details}")
        if details.get("profile_resolution", {}).get("fallback_allowed") is not False:
            raise AssertionError(f"Claude denial must not imply an unapproved fallback: {details}")
        if "/Users/" in reason or "execution_status" in reason or "exit_code" in reason:
            raise AssertionError(f"PreToolUse denial must stay redacted and not claim execution: {reason}")

        profile = {
            "version": 1,
            "default_effect": "DENY",
            "subject": {"id": "runtime-hook-test"},
            "grants": [{
                "id": "analytics.example.com",
                "kind": "external_service",
                "selector": "analytics.example.com",
                "operations": ["execute"],
                "constraints": {
                    "change_boundary_required": False,
                    "network_allowed": True,
                    "allowed_destinations": ["analytics.example.com"],
                    "allowed_ports": [8443],
                    "allowed_methods": ["GET"],
                    "allowed_paths": ["/v1/**"],
                },
            }],
            "authority": {"human_approval_granted": False, "merge_authorized": False,
                          "release_authorized": False, "protected_operation_authorized": False},
        }
        (profile_root / "profile.yaml").write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
        mismatch_payload = {
            **missing_payload,
            "tool_input": {"command": "curl https://analytics.example.com:443/private?token=synthetic-secret-value"},
        }
        mismatch = run("claude-code", mismatch_payload,
                       extra_env={"AIPS_RESOURCE_AUTHORIZATION_PROFILE": "profile.yaml"})
        mismatch_reason = mismatch["hookSpecificOutput"]["permissionDecisionReason"]
        if marker not in mismatch_reason:
            raise AssertionError(f"Claude denial omitted the destination constraint difference: {mismatch}")
        mismatch_details = json.loads(mismatch_reason.split(marker, 1)[1])
        expected_diff = {"port": {"actual": 443, "expected": [8443]},
                         "path": {"actual": "/private", "expected": ["/v1/**"]}}
        if mismatch_details.get("constraint_diff") != expected_diff:
            raise AssertionError(f"Claude Hook must expose only redacted failing destination fields: {mismatch_details}")
        if "synthetic-secret-value" in mismatch_reason or "execution_status" in mismatch_reason:
            raise AssertionError(f"PreToolUse denial leaked data or claimed execution: {mismatch_reason}")
    print("runtime_policy native hook lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
