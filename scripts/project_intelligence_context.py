"""Stable compact projection of a Project Intelligence context manifest."""
from __future__ import annotations

from pathlib import Path
from typing import Any

SOURCE_NAMES = {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GEMINI.md"}


def compact_context_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    context = manifest.get("context") or {}
    layers = context.get("layers") or {}
    retrieval = context.get("retrieval") or {}
    project_instructions = [path for path in context.get("project_native") or [] if Path(path).name in SOURCE_NAMES]
    return {
        "version": manifest.get("version"),
        "runtime": manifest.get("runtime"),
        "project": manifest.get("project"),
        "task": manifest.get("task"),
        "context": {
            "always": context.get("always") or [],
            "system_protocol_routes": context.get("system_protocol_routes") or {},
            "runtime_native": context.get("runtime_native") or [],
            "project_native": project_instructions,
            "source_scope": context.get("source_scope") or {},
            "intelligence_topics": context.get("intelligence_topics") or [],
            "project_core": (layers.get("core") or {}).get("summary"),
            "retrieval": {
                "status": retrieval.get("status"),
                "reason_code": retrieval.get("reason_code"),
                "remediation": retrieval.get("remediation"),
                "results": [
                    {key: item.get(key) for key in ("path", "start_line", "end_line", "reason", "snippet") if item.get(key) is not None}
                    for item in (retrieval.get("results") or [])[:4]
                ],
            },
            "on_demand_source_count": len(context.get("project_native") or []) - len(project_instructions),
        },
        "intelligence": manifest.get("intelligence"),
        "freshness": {key: (manifest.get("freshness") or {}).get(key) for key in ("status", "reasons", "affected_topics")},
        "requirements": manifest.get("requirements"),
        "fail_policy": manifest.get("fail_policy"),
    }
