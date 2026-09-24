#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
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
    layers = ctx.get("layers") or {}
    core = layers.get("core") or {}
    recall = layers.get("recall") or {}
    telemetry = layers.get("telemetry") or {}
    lines = [
        "AIPS TURN CONTEXT",
        f"project={project.get('root')} mode={project.get('mode')}",
        f"intelligence_store={project.get('intelligence_store')}",
        f"readiness={intelligence.get('readiness')} freshness={intelligence.get('freshness')}",
        f"mutation_likely={(data.get('task') or {}).get('mutation_likely')}",
        f"initialize_intelligence={req.get('initialize_intelligence')}",
        f"semantic_enrichment_required={req.get('semantic_enrichment_required')}",
        f"change_impact_required={req.get('change_impact_required')}",
        f"task_freshness={(layers.get('task_freshness') or {}).get('status')}",
        f"context_tokens_estimated={telemetry.get('total_estimated_tokens')} hard_budget={telemetry.get('hard_budget_tokens')}",
        f"project_core_derived={core.get('canonical') is False} source_digest={core.get('source_digest')}",
        f"fail_policy={fail.get('mode')}",
    ]
    if core.get("summary"):
        lines.append("project_core_summary=" + str(core["summary"])[:6400])
    if recall.get("temporal_assertions"):
        lines.append("active_temporal_assertions=" + ",".join(str(item.get("id")) for item in recall["temporal_assertions"] if item.get("id"))[:1000])
    if req.get("targeted_refresh"):
        lines.append("targeted_refresh=" + ",".join(req["targeted_refresh"][:12]))
    if ctx.get("project_native"):
        lines.append("project_sources=" + ",".join(ctx["project_native"][:12]))
    if ctx.get("intelligence_topics"):
        lines.append("intelligence_topics=" + ",".join(ctx["intelligence_topics"][:12]))

    retrieval = ctx.get("retrieval") or {}
    lines.append(f"retrieval_status={retrieval.get('status')}")
    if retrieval.get("reason_code"):
        lines.append(f"retrieval_error={retrieval.get('reason_code')}")
    if retrieval.get("remediation"):
        lines.append("retrieval_next_step=" + str(retrieval["remediation"])[:400])
    if req.get("retrieval_index_required"):
        lines.append("retrieval_index_required=True (Agent should run: aips intelligence index --project <project>)")
    retrieval_results = retrieval.get("results") or []
    if retrieval_results:
        lines.append("retrieval_evidence:")
        for item in retrieval_results[:4]:
            if item.get("type") == "history":
                pointer = f"commit:{item.get('commit')} {item.get('subject')}"
            else:
                pointer = f"{item.get('path')}:{item.get('start_line')}-{item.get('end_line')}"
            reasons = ",".join(item.get("reason") or [])
            lines.append(f"- {pointer} score={item.get('score')} reason={reasons}")
            snippet = str(item.get("snippet") or "").strip().replace("\x00", "")
            if snippet:
                compact = snippet[:900].replace("\n", "\n    ")
                lines.append("    " + compact)

    lines.append(
        "For existing-project mutation: satisfy Intelligence initialization/refresh/readiness, "
        "ensure Retrieval Intelligence when requested, resolve Change Impact, preserve valid native conventions, then implement."
    )
    hard_budget = max(1, int(telemetry.get("hard_budget_tokens") or 7600))
    truncated = False

    def estimate() -> int:
        return math.ceil(len("\n".join(lines)) / 4)

    while estimate() > hard_budget:
        index = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].startswith("    ")), None)
        if index is not None:
            lines.pop(index)
            truncated = True
            continue
        index = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].startswith("- ")), None)
        if index is not None:
            lines.pop(index)
            truncated = True
            continue
        index = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].startswith(("project_sources=", "intelligence_topics=", "targeted_refresh="))), None)
        if index is not None:
            key, _, value = lines[index].partition("=")
            entries = value.split(",")
            lines[index] = f"{key}=" + ",".join(entries[:4]) + f" (truncated:{max(0, len(entries) - 4)})"
            if len(entries) <= 4:
                lines.pop(index)
            truncated = True
            continue
        summary_index = next((i for i, line in enumerate(lines) if line.startswith("project_core_summary=")), None)
        if summary_index is not None and len(lines[summary_index]) > 80:
            line = lines[summary_index]
            lines[summary_index] = "project_core_summary=" + line[len("project_core_summary="): int(len(line) * 0.8)] + " [truncated]"
            truncated = True
            continue
        if estimate() <= hard_budget:
            break
        raise ValueError("mandatory turn context fields exceed the configured hard budget")

    rendered = "\n".join(lines)
    rendered_tokens = math.ceil(len(rendered) / 4)
    telemetry["rendered_tokens"] = rendered_tokens
    telemetry["rendered_budget_tokens"] = hard_budget
    telemetry["rendered_truncated"] = truncated
    for index, line in enumerate(lines):
        if line.startswith("context_tokens_estimated="):
            lines[index] = f"context_tokens_estimated={rendered_tokens} hard_budget={hard_budget} truncated={truncated}"
            break
    rendered = "\n".join(lines)
    if math.ceil(len(rendered) / 4) > hard_budget:
        raise ValueError("rendered turn context exceeds the configured hard budget")
    return rendered


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
