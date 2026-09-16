#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def aips_command() -> list[str]:
    aips = os.environ.get("AIPS_BIN", "aips")
    return [aips, "intelligence", "context"]


def resolve(runtime: str, prompt: str, project: str) -> dict:
    cmd = aips_command() + ["--runtime", runtime, "--project", project, "--prompt", prompt, "--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    if r.returncode != 0:
        return {"error": (r.stderr or r.stdout).strip(), "fail_policy": {"mode": "soft"}}
    return json.loads(r.stdout)


def compact_context(data: dict) -> str:
    if "error" in data:
        return f"AIPS turn context unavailable: {data['error']}"
    req = data.get("requirements") or {}
    ctx = data.get("context") or {}
    project = data.get("project") or {}
    lines = [
        "AIPS TURN CONTEXT",
        f"project={project.get('root')} mode={project.get('mode')}",
        f"intelligence_store={project.get('intelligence_store')}",
        f"freshness={(data.get('freshness') or {}).get('status')}",
        f"mutation_likely={(data.get('task') or {}).get('mutation_likely')}",
        f"initialize_intelligence={req.get('initialize_intelligence')}",
        f"change_impact_required={req.get('change_impact_required')}",
    ]
    if req.get("targeted_refresh"):
        lines.append("targeted_refresh=" + ",".join(req["targeted_refresh"][:12]))
    if ctx.get("project_native"):
        lines.append("project_sources=" + ",".join(ctx["project_native"][:12]))
    if ctx.get("intelligence_topics"):
        lines.append("intelligence_topics=" + ",".join(ctx["intelligence_topics"][:12]))
    lines.append("Before mutating an existing project: initialize/refresh required Intelligence, load relevant sources, create Change Impact, then preserve valid project-native conventions.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True, choices=["gemini-cli", "claude-code"])
    args = parser.parse_args()
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    prompt = str(payload.get("prompt") or payload.get("user_prompt") or "")
    project = (
        os.environ.get("GEMINI_PROJECT_DIR")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.environ.get("GEMINI_CWD")
        or os.getcwd()
    )
    try:
        data = resolve(args.runtime, prompt, project)
    except Exception as exc:
        data = {"error": str(exc), "fail_policy": {"mode": "soft"}}
    additional = compact_context(data)

    if args.runtime == "gemini-cli":
        print(json.dumps({"hookSpecificOutput": {"additionalContext": additional}}, ensure_ascii=False))
    else:
        # Claude Code UserPromptSubmit hooks accept additionalContext in hookSpecificOutput.
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": additional}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
