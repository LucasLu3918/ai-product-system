#!/usr/bin/env python3
"""Durable Issue formatting and monthly roll-up for Evolution Radar."""

from __future__ import annotations

import argparse
import calendar
import json
from pathlib import Path
from typing import Any

import yaml

from evolution_radar import evidence_quality_metadata, validate_config, validate_evidence

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
            source_id = str(signal.get("source_id") or "")
            source_ids = list(signal.get("source_ids") or ([source_id] if source_id else []))
            source_roles = list(
                signal.get("source_roles")
                or ([signal.get("source_role")] if signal.get("source_role") else ["legacy"])
            )
            if fp not in seen:
                item = dict(signal)
                item["recurrence_count"] = int(item.get("recurrence_count") or 1)
                item["duplicate_of"] = None
                item["source_ids"] = sorted(set(str(x) for x in source_ids if x))
                item["source_roles"] = sorted(set(str(x) for x in source_roles if x))
                provenance = signal.get("source_provenance") or [
                    {"source_id": sid, "role": str(signal.get("source_role") or source_roles[0] if source_roles else "legacy")}
                    for sid in source_ids
                ]
                item["source_provenance"] = [
                    {"source_id": str(value.get("source_id") or ""), "role": str(value.get("role") or "legacy")}
                    for value in provenance
                    if isinstance(value, dict) and str(value.get("source_id") or "")
                ]
                seen[fp] = item
            else:
                seen[fp]["recurrence_count"] += int(signal.get("recurrence_count") or 1)
                seen[fp]["source_ids"] = sorted(set(seen[fp].get("source_ids") or []) | set(str(x) for x in source_ids if x))
                seen[fp]["source_roles"] = sorted(set(seen[fp].get("source_roles") or []) | set(str(x) for x in source_roles if x))
                existing_provenance = {
                    (str(value.get("source_id") or ""), str(value.get("role") or "legacy"))
                    for value in (seen[fp].get("source_provenance") or [])
                    if isinstance(value, dict) and str(value.get("source_id") or "")
                }
                incoming_provenance = signal.get("source_provenance") or [
                    {"source_id": sid, "role": str(signal.get("source_role") or source_roles[0] if source_roles else "legacy")}
                    for sid in source_ids
                ]
                for value in incoming_provenance:
                    if isinstance(value, dict) and str(value.get("source_id") or ""):
                        existing_provenance.add((str(value["source_id"]), str(value.get("role") or "legacy")))
                seen[fp]["source_provenance"] = [
                    {"source_id": source_id, "role": role}
                    for source_id, role in sorted(existing_provenance)
                ]

    for item in seen.values():
        roles = set(item.get("source_roles") or ["legacy"])
        if "primary" in roles and "community" in roles:
            item["verification_status"] = "PRIMARY_CORROBORATED"
        elif "primary" in roles:
            item["verification_status"] = "PRIMARY_SOURCE"
        elif "community" in roles:
            item["verification_status"] = "DISCOVERY_ONLY"
        else:
            item["verification_status"] = "LEGACY_UNVERIFIED"
        provenance = item.get("source_provenance") or [
            {"source_id": sid, "role": next(iter(roles), "legacy")}
            for sid in item.get("source_ids") or []
        ]
        item["source_provenance"] = sorted(
            provenance,
            key=lambda value: (str(value.get("source_id") or ""), str(value.get("role") or "")),
        )
        item.update(evidence_quality_metadata(item["source_provenance"]))
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


def _monday_dates(period: str) -> list[str]:
    year, month = (int(part) for part in period.split("-", 1))
    days = calendar.monthrange(year, month)[1]
    return [
        f"{year:04d}-{month:02d}-{day:02d}"
        for day in range(1, days + 1)
        if calendar.weekday(year, month, day) == calendar.MONDAY
    ]


def _weekly_generated_date(doc: dict[str, Any]) -> str | None:
    generated_at = str((doc.get("run") or {}).get("generated_at") or "")
    return generated_at[:10] if len(generated_at) >= 10 else None


def _pipeline_health(
    docs: list[dict[str, Any]], *, expected: list[str], expected_kind: str
) -> dict[str, Any]:
    observed = sorted(
        {day for doc in docs if (day := _weekly_generated_date(doc)) is not None}
    )
    missing = sorted(set(expected) - set(observed))
    duplicate_dates = sorted(
        day for day in set(observed)
        if sum(_weekly_generated_date(doc) == day for doc in docs) > 1
    )
    source_gaps: list[str] = []
    for doc in docs:
        sources = doc.get("sources") or {}
        configured = set(sources.get("configured") or [])
        attempted = set(sources.get("attempted") or [])
        failed = {
            str(item.get("source_id") or item.get("source") or "")
            for item in (sources.get("failures") or [])
            if isinstance(item, dict)
        }
        unaccounted = sorted(configured - attempted - failed)
        if unaccounted:
            source_gaps.extend(unaccounted)
    reasons = []
    if not expected:
        reasons.append("expected_cohort_unknown")
    if missing:
        reasons.append("scheduled_runs_missing")
    if duplicate_dates:
        reasons.append("duplicate_run_dates")
    if source_gaps:
        reasons.append("configured_sources_unaccounted")
    if any((doc.get("sources") or {}).get("failures") for doc in docs):
        reasons.append("source_collection_failures")
    return {
        "status": "COMPLETE" if not reasons else "INCOMPLETE_INPUT",
        "expected_kind": expected_kind,
        "expected_count": len(expected),
        "expected_dates": expected,
        "observed_count": len(docs),
        "observed_dates": observed,
        "missing_dates": missing,
        "duplicate_dates": duplicate_dates,
        "source_gaps": sorted(set(source_gaps)),
        "reasons": reasons,
    }


def _content_value(
    docs: list[dict[str, Any]], *, complete: bool, minimum_signals: int
) -> dict[str, Any]:
    signal_count = sum(
        int((doc.get("summary") or {}).get("signal_count") or len(doc.get("signals") or []))
        for doc in docs
    )
    recommendations = [
        recommendation
        for doc in docs
        for recommendation in (doc.get("recommendations") or [])
        if isinstance(recommendation, dict)
    ]
    actionable_states = {"ASSESS", "TRIAL", "ADOPT"}
    actionable_count = sum(
        recommendation.get("state") in actionable_states
        for recommendation in recommendations
    )
    semantic_pending = any(
        recommendation.get("state") == "ANALYSIS_PENDING"
        for recommendation in recommendations
    )
    if not complete:
        status = "INCOMPLETE_INPUT"
    elif semantic_pending:
        status = "SEMANTIC_ANALYSIS_PENDING"
    elif actionable_count:
        status = "ACTIONABLE_CANDIDATE_READY"
    elif signal_count < minimum_signals:
        status = "SOURCE_YIELD_LOW"
    else:
        status = "HEALTHY_NO_ACTIONABLE_SIGNAL"
    return {
        "status": status,
        "signal_count": signal_count,
        "actionable_count": actionable_count,
        "semantic_pending_count": sum(
            recommendation.get("state") == "ANALYSIS_PENDING"
            for recommendation in recommendations
        ),
        "minimum_signals_for_yield_assessment": minimum_signals,
    }


def _recommendations_from_docs(
    docs: list[dict[str, Any]], signals: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for doc in sorted(docs, key=lambda item: str((item.get("run") or {}).get("generated_at") or "")):
        for recommendation in doc.get("recommendations") or []:
            if isinstance(recommendation, dict) and recommendation.get("signal_fingerprint"):
                latest[str(recommendation["signal_fingerprint"])] = dict(recommendation)
    return [
        latest.get(str(signal.get("fingerprint")))
        or pending_recommendations([signal])[0]
        for signal in signals
    ]


def _analyzer_status(docs: list[dict[str, Any]]) -> str:
    if any(
        isinstance(recommendation, dict)
        and recommendation.get("state") != "ANALYSIS_PENDING"
        for doc in docs
        for recommendation in (doc.get("recommendations") or [])
    ):
        return "available"
    return "unavailable"


def monthly_rollup(
    issues: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    period: str | None = None,
    minimum_source_signals: int = 8,
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
        doc = extract_evidence(str(issue.get("body") or ""))
        run_period = ((doc or {}).get("run") or {}).get("period")
        generated_date = _weekly_generated_date(doc or {})
        if period is None:
            in_period = True
        elif run_period:
            in_period = run_period == period
        elif generated_date:
            in_period = generated_date.startswith(period + "-")
        else:
            in_period = str(issue.get("created_at") or "").startswith(period + "-")
        if doc and in_period and (doc.get("run") or {}).get("mode") == "weekly":
            weekly_docs.append(doc)

    signals = aggregate_signals(weekly_docs)
    recommendations = _recommendations_from_docs(weekly_docs, signals)
    expected_dates = _monday_dates(period) if period else []
    health = _pipeline_health(weekly_docs, expected=expected_dates, expected_kind="weekly_monday")
    minimum_signals = int(minimum_source_signals)
    value = _content_value(weekly_docs, complete=health["status"] == "COMPLETE", minimum_signals=minimum_signals)
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
            "pipeline_health": health,
            "content_value": value,
            "analyzer": {"status": _analyzer_status(weekly_docs), "provider": None, "model": None},
        },
        "sources": {"configured": configured, "attempted": attempted, "failures": failures},
        "signals": signals,
        "recommendations": recommendations,
        "summary": {
            "signal_count": sum(len(d.get("signals") or []) for d in weekly_docs),
            "adopt_minimum_evidence_level": int((config.get("policy") or {}).get("evidence_quality", {}).get("adopt_minimum_level", 2)),
            "deduplicated_count": len(signals),
            "recommendation_count": len(recommendations),
            "actionable_count": value["actionable_count"],
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



def quarter_months(period: str) -> list[str]:
    if not (len(period) == 7 and period[:4].isdigit() and period[4:6] == "-Q" and period[6] in "1234"):
        raise ValueError("period must be YYYY-QN")
    year = int(period[:4])
    quarter = int(period[6])
    start = 1 + (quarter - 1) * 3
    return [f"{year:04d}-{month:02d}" for month in range(start, start + 3)]


def quarterly_rollup(
    issues: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    period: str,
    minimum_source_signals: int = 8,
) -> dict[str, Any]:
    errors = validate_config(config)
    if errors:
        raise ValueError("; ".join(errors))
    months = quarter_months(period)

    monthly_docs: list[dict[str, Any]] = []
    for issue in issues:
        if not str(issue.get("title") or "").startswith("Evolution Radar [monthly]"):
            continue
        doc = extract_evidence(str(issue.get("body") or ""))
        run = (doc or {}).get("run") or {}
        if doc and run.get("mode") == "monthly" and run.get("period") in months:
            monthly_docs.append(doc)

    signals = aggregate_signals(monthly_docs)
    recommendations = _recommendations_from_docs(monthly_docs, signals)
    configured = [s["id"] for s in config.get("sources") or [] if s.get("enabled", True)]
    attempted = sorted({x for d in monthly_docs for x in ((d.get("sources") or {}).get("attempted") or [])})
    failures = [x for d in monthly_docs for x in ((d.get("sources") or {}).get("failures") or [])]
    month_counts = {
        month: sum(1 for doc in monthly_docs if (doc.get("run") or {}).get("period") == month)
        for month in months
    }
    missing_months = [month for month, count in month_counts.items() if count == 0]
    duplicate_months = [month for month, count in month_counts.items() if count > 1]
    monthly_health = [(doc.get("run") or {}).get("pipeline_health") or {} for doc in monthly_docs]
    health_reasons = []
    if missing_months:
        health_reasons.append("monthly_bundles_missing")
    if duplicate_months:
        health_reasons.append("duplicate_monthly_bundles")
    if not monthly_health or any(item.get("status") != "COMPLETE" for item in monthly_health):
        health_reasons.append("monthly_pipeline_incomplete_or_unverified")
    health = {
        "status": "COMPLETE" if not health_reasons else "INCOMPLETE_INPUT",
        "expected_kind": "calendar_month",
        "expected_count": 3,
        "expected_months": months,
        "observed_count": len(monthly_docs),
        "observed_month_counts": month_counts,
        "missing_months": missing_months,
        "duplicate_months": duplicate_months,
        "reasons": health_reasons,
    }
    minimum_signals = 3 * int(minimum_source_signals)
    value = _content_value(monthly_docs, complete=health["status"] == "COMPLETE", minimum_signals=minimum_signals)
    return {
        "version": 1,
        "run": {
            "mode": "quarterly",
            "generated_at": None,
            "repository_revision": None,
            "period": period,
            "months_reviewed": months,
            "monthly_evidence_count": len(monthly_docs),
            "pipeline_health": health,
            "content_value": value,
            "analyzer": {"status": _analyzer_status(monthly_docs), "provider": None, "model": None},
        },
        "sources": {"configured": configured, "attempted": attempted, "failures": failures},
        "signals": signals,
        "recommendations": recommendations,
        "summary": {
            "signal_count": sum(int((d.get("summary") or {}).get("signal_count") or 0) for d in monthly_docs),
            "adopt_minimum_evidence_level": int((config.get("policy") or {}).get("evidence_quality", {}).get("adopt_minimum_level", 2)),
            "deduplicated_count": len(signals),
            "recommendation_count": len(recommendations),
            "actionable_count": value["actionable_count"],
            "zero_recommendations_valid": True,
        },
        "pipeline_health": health,
        "content_value": value,
        "authority": {
            "code_change_authorized": False,
            "branch_or_pr_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "human_decision_required": True,
        },
    }

def issue_markdown(
    doc: dict[str, Any],
    handoff_text: str | None = None,
    preanalysis_text: str | None = None,
    analysis_text: str | None = None,
) -> str:
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
    coverage = sources.get("community_coverage") or {}
    if coverage:
        lines.append(
            f"- Community coverage: {coverage.get('successful', 0)}/{coverage.get('target', 0)} "
            f"(required {coverage.get('required', 0)}) — {coverage.get('status')}"
        )
    if "global_signal_limit" in summary:
        lines.append(
            f"- Weekly raw signal budget: {summary.get('signal_count', 0)}/{summary.get('global_signal_limit', 0)} "
            f"(collected before cap: {summary.get('collected_before_global_limit', 0)})"
        )
    if mode == "monthly":
        if run.get("period"):
            lines.append(f"- Review period: {run.get('period')}")
        lines.append(f"- Weekly evidence bundles reviewed: {run.get('weekly_evidence_count', 0)}")
    if run.get("pipeline_health"):
        lines.append(f"- Pipeline health: `{run['pipeline_health'].get('status')}`")
    if run.get("content_value"):
        lines.append(f"- Content value: `{run['content_value'].get('status')}`")
    if mode == "quarterly":
        if run.get("period"):
            lines.append(f"- Review quarter: {run.get('period')}")
        lines.append(f"- Monthly evidence bundles reviewed: {run.get('monthly_evidence_count', 0)}")
        lines.append(f"- Calendar months reviewed: {', '.join(run.get('months_reviewed') or [])}")
    lines += [
        f"- Semantic assessment: `{run.get('content_value', {}).get('status', 'ANALYSIS_PENDING')}`",
        "",
        "This report is evidence/recommendation input only. It does not authorize code changes, PRs, merges or releases.",
        "",
    ]
    if preanalysis_text:
        lines += [preanalysis_text.rstrip(), ""]
    if handoff_text:
        lines += [handoff_text.rstrip(), ""]
    if analysis_text:
        lines += [analysis_text.rstrip(), ""]
    lines += [
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
    rollup.add_argument("--effectiveness-config", default="config/evolution-effectiveness.yaml")
    rollup.add_argument("--output", required=True)
    quarterly = sub.add_parser("quarterly-rollup")
    quarterly.add_argument("--issues-json", required=True)
    quarterly.add_argument("--config", required=True)
    quarterly.add_argument("--period", required=True)
    quarterly.add_argument("--effectiveness-config", default="config/evolution-effectiveness.yaml")
    quarterly.add_argument("--output", required=True)
    issue = sub.add_parser("issue-body")
    issue.add_argument("evidence")
    issue.add_argument("--handoff")
    issue.add_argument("--preanalysis")
    issue.add_argument("--analysis")
    issue.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.command == "monthly-rollup":
        raw_issues = json.loads(Path(args.issues_json).read_text(encoding="utf-8"))
        issues = flatten_issue_pages(raw_issues)
        config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
        effectiveness_config = yaml.safe_load(Path(args.effectiveness_config).read_text(encoding="utf-8")) or {}
        minimum = int((effectiveness_config.get("review_flags") or {}).get("minimum_source_signals", 8))
        doc = monthly_rollup(issues, config, period=args.period, minimum_source_signals=minimum)
        Path(args.output).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return 0

    if args.command == "quarterly-rollup":
        raw_issues = json.loads(Path(args.issues_json).read_text(encoding="utf-8"))
        issues = flatten_issue_pages(raw_issues)
        config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
        effectiveness_config = yaml.safe_load(Path(args.effectiveness_config).read_text(encoding="utf-8")) or {}
        minimum = int((effectiveness_config.get("review_flags") or {}).get("minimum_source_signals", 8))
        doc = quarterly_rollup(issues, config, period=args.period, minimum_source_signals=minimum)
        Path(args.output).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return 0

    doc = yaml.safe_load(Path(args.evidence).read_text(encoding="utf-8")) or {}
    errors = validate_evidence(doc)
    if errors:
        raise ValueError("invalid evidence: " + "; ".join(errors))
    handoff_text = Path(args.handoff).read_text(encoding="utf-8") if args.handoff else None
    preanalysis_text = Path(args.preanalysis).read_text(encoding="utf-8") if args.preanalysis else None
    analysis_text = None
    if args.analysis:
        from evolution_analysis import analysis_markdown, validate_analysis

        analysis = yaml.safe_load(Path(args.analysis).read_text(encoding="utf-8")) or {}
        errors = validate_analysis(doc, analysis)
        if errors:
            raise ValueError("invalid analysis: " + "; ".join(errors))
        analysis_text = analysis_markdown(analysis)
    Path(args.output).write_text(issue_markdown(doc, handoff_text, preanalysis_text, analysis_text), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
