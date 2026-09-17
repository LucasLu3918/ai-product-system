#!/usr/bin/env python3
"""Durable Issue formatting and monthly roll-up for Evolution Radar."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from evolution_radar import validate_config, validate_evidence

EVIDENCE_START = "<!-- AIPS_EVOLUTION_EVIDENCE_START -->"
EVIDENCE_END = "<!-- AIPS_EVOLUTION_EVIDENCE_END -->"


def extract_evidence(body: str) -> dict[str, Any] | None:
    if EVIDENCE_START not in body or EVIDENCE_END not in body:
        return None
    payload = body.split(EVIDENCE_START, 1)[1].split(EVIDENCE_END, 1)[0].strip()
    if payload.startswith("```yaml"):
        payload = payload[len("```yaml"):].strip()
    if payload.endswith("```"):
        payload = payload[:-3].strip()
    try:
        doc = yaml.safe_load(payload) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(doc, dict) or validate_evidence(doc):
        return None
    return doc


def flatten_issue_pages(value: Any) -> list[dict[str, Any]]:
    """Accept one GitHub Issues page or gh api --paginate --slurp pages."""
    if not isinstance(value, list):
        raise ValueError("issues JSON must be an array")
    if not value:
        return []
    if all(isinstance(item, dict) for item in value):
        return value
    if all(isinstance(page, list) for page in value):
        issues: list[dict[str, Any]] = []
        for page in value:
            if not all(isinstance(item, dict) for item in page):
                raise ValueError("issues JSON pages must contain issue objects")
            issues.extend(page)
        return issues
    raise ValueError("issues JSON must be an issue array or an array of issue pages")


def aggregate_signals(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for doc in docs:
        for signal in doc.get("signals") or []:
            fp = signal.get("fingerprint")
            if not fp:
                continue
            if fp not in seen:
                item = dict(signal)
                item["recurrence_count"] = int(item.get("recurrence_count") or 1)
                item["duplicate_of"] = None
                seen[fp] = item
            else:
                seen[fp]["recurrence_count"] += int(signal.get("recurrence_count") or 1)
    return list(seen.values())


def pending_recommendations(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "signal_fingerprint": signal["fingerprint"],
            "state": "ANALYSIS_PENDING",
            "aips_current_state": "",
            "benefit": "",
            "cost_complexity": "",
            "reliability_security": "",
            "confidence": None,
            "uncertainty": "Semantic analyzer unavailable; no suitability conclusion inferred.",
            "example": "",
            "reuse_extension_path": [],
            "architecture_diagram_review_if_adopted": False,
        }
        for signal in signals
    ]


def monthly_rollup(
    issues: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    period: str | None = None,
) -> dict[str, Any]:
    errors = validate_config(config)
    if errors:
        raise ValueError("; ".join(errors))
    if period is not None and not (len(period) == 7 and period[4] == "-" and period.replace("-", "").isdigit()):
        raise ValueError("period must be YYYY-MM")

    weekly_docs: list[dict[str, Any]] = []
    for issue in issues:
        if not str(issue.get("title") or "").startswith("Evolution Radar [weekly]"):
            continue
        if period is not None and not str(issue.get("created_at") or "").startswith(period + "-"):
            continue
        doc = extract_evidence(str(issue.get("body") or ""))
        if doc and (doc.get("run") or {}).get("mode") == "weekly":
            weekly_docs.append(doc)

    signals = aggregate_signals(weekly_docs)
    recommendations = pending_recommendations(signals)
    configured = [s["id"] for s in config.get("sources") or [] if s.get("enabled", True)]
    attempted = sorted({x for d in weekly_docs for x in ((d.get("sources") or {}).get("attempted") or [])})
    failures = [x for d in weekly_docs for x in ((d.get("sources") or {}).get("failures") or [])]
    return {
        "version": 1,
        "run": {
            "mode": "monthly",
            "generated_at": None,
            "repository_revision": None,
            "period": period,
            "weekly_evidence_count": len(weekly_docs),
            "analyzer": {"status": "unavailable", "provider": None, "model": None},
        },
        "sources": {"configured": configured, "attempted": attempted, "failures": failures},
        "signals": signals,
        "recommendations": recommendations,
        "summary": {
            "signal_count": sum(len(d.get("signals") or []) for d in weekly_docs),
            "deduplicated_count": len(signals),
            "recommendation_count": len(recommendations),
            "actionable_count": 0,
            "zero_recommendations_valid": True,
        },
        "authority": {
            "code_change_authorized": False,
            "branch_or_pr_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "human_decision_required": True,
        },
    }


def issue_markdown(doc: dict[str, Any]) -> str:
    summary = doc.get("summary") or {}
    sources = doc.get("sources") or {}
    run = doc.get("run") or {}
    mode = run.get("mode")
    lines = [
        f"## Evolution Radar — {mode}",
        "",
        f"- Signals observed: {summary.get('signal_count', 0)}",
        f"- Unique signals: {summary.get('deduplicated_count', 0)}",
        f"- Actionable recommendations: {summary.get('actionable_count', 0)}",
        f"- Source failures: {len(sources.get('failures') or [])}",
    ]
    if mode == "monthly":
        if run.get("period"):
            lines.append(f"- Review period: {run.get('period')}")
        lines.append(f"- Weekly evidence bundles reviewed: {run.get('weekly_evidence_count', 0)}")
    lines += [
        "- Semantic assessment: `ANALYSIS_PENDING` when no analyzer is configured",
        "",
        "This report is evidence/recommendation input only. It does not authorize code changes, PRs, merges or releases.",
        "",
        EVIDENCE_START,
        "```yaml",
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).rstrip(),
        "```",
        EVIDENCE_END,
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    rollup = sub.add_parser("monthly-rollup")
    rollup.add_argument("--issues-json", required=True)
    rollup.add_argument("--config", required=True)
    rollup.add_argument("--period")
    rollup.add_argument("--output", required=True)
    issue = sub.add_parser("issue-body")
    issue.add_argument("evidence")
    issue.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.command == "monthly-rollup":
        raw_issues = json.loads(Path(args.issues_json).read_text(encoding="utf-8"))
        issues = flatten_issue_pages(raw_issues)
        config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
        doc = monthly_rollup(issues, config, period=args.period)
        Path(args.output).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return 0

    doc = yaml.safe_load(Path(args.evidence).read_text(encoding="utf-8")) or {}
    errors = validate_evidence(doc)
    if errors:
        raise ValueError("invalid evidence: " + "; ".join(errors))
    Path(args.output).write_text(issue_markdown(doc), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
