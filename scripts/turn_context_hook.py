#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def resolve(runtime: str, prompt: str, project: str) -> dict:
    aips = os.environ.get("AIPS_BIN", "aips")
    cmd = [
        aips, "intelligence", "context",
        "--runtime", runtime,
        "--project", project,
        "--prompt", prompt,
        "--format", "json",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    if r.returncode != 0:
        return {
            "error": (r.stderr or r.stdout).strip(),
            "fail_policy": {"mode": "soft"},
        }
    return json.loads(r.stdout)


def compact_context(data: dict) -> str:
    if "error" in data:
        return f"AIPS turn context unavailable: {data['error']}"
    req = data.get("requirements") or {}
    ctx = data.get("context") or {}
    project = data.get("project") or {}
    intelligence = data.get("intelligence") or {}
    fail = data.get("fail_policy") or {}
    lines = [
        "AIPS TURN CONTEXT",
        f"project={project.get('root')} mode={project.get('mode')}",
        f"intelligence_store={project.get('intelligence_store')}",
        f"readiness={intelligence.get('readiness')} freshness={intelligence.get('freshness')}",
        f"mutation_likely={(data.get('task') or {}).get('mutation_likely')}",
        f"initialize_intelligence={req.get('initialize_intelligence')}",
        f"semantic_enrichment_required={req.get('semantic_enrichment_required')}",
        f"change_impact_required={req.get('change_impact_required')}",
        f"fail_policy={fail.get('mode')}",
    ]
    if req.get("targeted_refresh"):
        lines.append("targeted_refresh=" + ",".join(req["targeted_refresh"][:12]))
    if ctx.get("project_native"):
        lines.append("project_sources=" + ",".join(ctx["project_native"][:12]))
    if ctx.get("intelligence_topics"):
        lines.append("intelligence_topics=" + ",".join(ctx["intelligence_topics"][:12]))
    lines.append(
        "For existing-project mutation: satisfy Intelligence initialization/refresh/readiness, "
        "resolve Change Impact, preserve valid native conventions, then implement."
    )
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
        print(json.dumps(
            {"hookSpecificOutput": {"additionalContext": additional}},
            ensure_ascii=False,
        ))
    else:
        # Claude Code UserPromptSubmit supports plain stdout as prompt context;
        # use the simpler compatible form rather than requiring JSON hook fields.
        print(additional)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
