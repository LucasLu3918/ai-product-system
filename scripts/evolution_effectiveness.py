#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

EVIDENCE_START = "<!-- AIPS_EVOLUTION_EVIDENCE_START -->"
EVIDENCE_END = "<!-- AIPS_EVOLUTION_EVIDENCE_END -->"
PREANALYSIS_START = "<!-- AIPS_EVOLUTION_PREANALYSIS_START -->"
PREANALYSIS_END = "<!-- AIPS_EVOLUTION_PREANALYSIS_END -->"
ANALYSIS_START = "<!-- AIPS_EVOLUTION_ANALYSIS_START -->"
ANALYSIS_END = "<!-- AIPS_EVOLUTION_ANALYSIS_END -->"
DECISION_START = "<!-- AIPS_EVOLUTION_DECISION_START -->"
DECISION_END = "<!-- AIPS_EVOLUTION_DECISION_END -->"
TRIAL_HANDOFF_START = "<!-- AIPS_EVOLUTION_TRIAL_HANDOFF_START -->"
TRIAL_HANDOFF_END = "<!-- AIPS_EVOLUTION_TRIAL_HANDOFF_END -->"
TRIAL_START = "<!-- AIPS_EVOLUTION_TRIAL_START -->"
TRIAL_END = "<!-- AIPS_EVOLUTION_TRIAL_END -->"
ADOPTION_START = "<!-- AIPS_EVOLUTION_ADOPTION_START -->"
ADOPTION_END = "<!-- AIPS_EVOLUTION_ADOPTION_END -->"
EFFECTIVENESS_START = "<!-- AIPS_EVOLUTION_EFFECTIVENESS_START -->"
EFFECTIVENESS_END = "<!-- AIPS_EVOLUTION_EFFECTIVENESS_END -->"


def load_mapping(path: str | Path) -> dict[str, Any]:
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _strip_fence(payload: str) -> str:
    lines = payload.strip().splitlines()
    if lines and (lines[0].strip().startswith("```") or lines[0].strip().startswith("~~~")):
        lines = lines[1:]
    if lines and (lines[-1].strip().startswith("```") or lines[-1].strip().startswith("~~~")):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def extract_all(text: str, start: str, end: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    rest = str(text or "")
    while start in rest and end in rest:
        after = rest.split(start, 1)[1]
        payload, tail = after.split(end, 1)
        parsed = yaml.safe_load(_strip_fence(payload)) or {}
        if isinstance(parsed, dict):
            out.append(parsed)
        rest = tail
    return out


def _flatten_issues(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        if raw and all(isinstance(item, list) for item in raw):
            return [issue for page in raw for issue in page if isinstance(issue, dict)]
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        for key in ("issues", "items"):
            value = raw.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _comments(issue: dict[str, Any]) -> list[dict[str, Any]]:
    value = issue.get("comments") or []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("nodes", "items"):
            nodes = value.get(key)
            if isinstance(nodes, list):
                return [item for item in nodes if isinstance(item, dict)]
    return []


def _text_blobs(issue: dict[str, Any]) -> list[str]:
    blobs = [str(issue.get("body") or "")]
    blobs.extend(str(comment.get("body") or "") for comment in _comments(issue))
    return blobs


def _issue_number(issue: dict[str, Any]) -> int:
    value = issue.get("number", issue.get("issue_number", 0))
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _weekly_evidence(issue: dict[str, Any]) -> dict[str, Any] | None:
    docs = extract_all(str(issue.get("body") or ""), EVIDENCE_START, EVIDENCE_END)
    for doc in docs:
        if ((doc.get("run") or {}).get("mode")) == "weekly":
            return doc
    return None


def _run_month(evidence: dict[str, Any], issue: dict[str, Any]) -> str:
    generated = str((evidence.get("run") or {}).get("generated_at") or "")
    if len(generated) >= 7:
        return generated[:7]
    created = str(issue.get("createdAt") or issue.get("created_at") or "")
    return created[:7] if len(created) >= 7 else ""


def select_cohort(issues: list[dict[str, Any]], period: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    selected: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for issue in issues:
        evidence = _weekly_evidence(issue)
        if evidence is None:
            continue
        if _run_month(evidence, issue) == period:
            selected.append((issue, evidence))
    selected.sort(key=lambda pair: _issue_number(pair[0]))
    return selected


def _source_ids(signal: dict[str, Any]) -> list[str]:
    ids = [str(x) for x in (signal.get("source_ids") or []) if str(x)]
    if not ids:
        for item in signal.get("source_provenance") or []:
            if isinstance(item, dict) and str(item.get("source_id") or ""):
                ids.append(str(item["source_id"]))
    source_id = str(signal.get("source_id") or "")
    if source_id and source_id not in ids:
        ids.append(source_id)
    return sorted(set(ids))


def _failure_source_id(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("source_id") or value.get("id") or "")
    text = str(value or "")
    if ":" in text:
        return text.split(":", 1)[0].strip()
    return text.strip()


def _bp(numerator: int, denominator: int) -> int | None:
    if denominator <= 0:
        return None
    return (int(numerator) * 10000) // int(denominator)


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if config.get("version") != 1:
        errors.append("effectiveness config version must be 1")
    cohort = config.get("cohort") or {}
    if cohort.get("mode") != "monthly":
        errors.append("effectiveness cohort.mode must be monthly")
    if cohort.get("evidence_modes") != ["weekly"]:
        errors.append("effectiveness cohort.evidence_modes must be [weekly]")
    metrics = config.get("metrics") or {}
    if metrics.get("actionable_states") != ["ASSESS", "TRIAL", "ADOPT"]:
        errors.append("effectiveness actionable_states must be ASSESS/TRIAL/ADOPT")
    flags = config.get("review_flags") or {}
    for key in (
        "minimum_source_runs",
        "minimum_source_signals",
        "low_shortlist_yield_basis_points_below",
        "high_failure_rate_basis_points_above",
        "zero_actionable_semantic_minimum",
    ):
        value = flags.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"review_flags.{key} must be a non-negative integer")
    authority = config.get("authority") or {}
    for key in (
        "automatic_source_weight_changes",
        "automatic_source_enable_disable",
        "automatic_config_mutation",
        "code_change_authorized",
        "branch_or_pr_authorized",
        "merge_authorized",
        "release_authorized",
    ):
        if authority.get(key) is not False:
            errors.append(f"authority.{key} must be false")
    if authority.get("human_review_required_for_source_changes") is not True:
        errors.append("source changes must remain Human-reviewed")
    return errors


def _init_source(source_id: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "configured_runs": 0,
        "attempted_runs": 0,
        "failure_count": 0,
        "collected_signal_count": 0,
        "shortlist_signal_count": 0,
        "semantic_signal_count": 0,
        "actionable_recommendation_count": 0,
        "trial_decision_count": 0,
        "trial_pass_count": 0,
        "adoption_count": 0,
    }


def _add_for_signal(
    source_metrics: dict[str, dict[str, Any]],
    signal_sources: dict[str, list[str]],
    fingerprint: str,
    field: str,
) -> None:
    for source_id in signal_sources.get(fingerprint, []):
        source_metrics.setdefault(source_id, _init_source(source_id))[field] += 1


def build_report(
    raw_issues: Any,
    config: dict[str, Any],
    *,
    period: str,
    repository_revision: str,
    generated_at: str,
) -> dict[str, Any]:
    errors = validate_config(config)
    if errors:
        raise ValueError("invalid effectiveness config: " + "; ".join(errors))
    if len(period) != 7 or period[4] != "-" or not period.replace("-", "").isdigit():
        raise ValueError("period must be YYYY-MM")
    if len(repository_revision) != 40:
        raise ValueError("repository_revision must be a 40-character git SHA")

    cohort = select_cohort(_flatten_issues(raw_issues), period)
    source_metrics: dict[str, dict[str, Any]] = {}
    signal_sources: dict[str, list[str]] = {}

    raw_signal_count = 0
    unique_signal_count = 0
    shortlist_count = 0
    semantic_signal_count = 0
    semantic_state_counts = {state: 0 for state in ("COVERED", "HOLD", "ASSESS", "TRIAL", "ADOPT", "ANALYSIS_PENDING")}
    decision_counts = {state: 0 for state in ("REJECT", "HOLD", "ASSESS", "TRIAL", "ADOPT")}
    trial_status_counts = {state: 0 for state in ("PASS", "FAIL", "BLOCKED")}
    trial_handoff_count = 0
    adoption_count = 0

    seen_decisions: set[str] = set()
    seen_trials: set[str] = set()
    seen_handoffs: set[str] = set()
    seen_adoptions: set[str] = set()
    input_manifest: list[dict[str, Any]] = []

    for issue, evidence in cohort:
        issue_number = _issue_number(issue)
        body = str(issue.get("body") or "")
        blobs = _text_blobs(issue)
        input_manifest.append({
            "issue_number": issue_number,
            "issue_digest": canonical_digest({
                "title": str(issue.get("title") or ""),
                "body": body,
                "comments": [str(comment.get("body") or "") for comment in _comments(issue)],
            }),
        })

        summary = evidence.get("summary") or {}
        signals = [item for item in (evidence.get("signals") or []) if isinstance(item, dict)]
        raw_signal_count += int(summary.get("signal_count") or len(signals))
        unique_signal_count += int(summary.get("deduplicated_count") or len(signals))

        sources = evidence.get("sources") or {}
        configured = [str(x) for x in (sources.get("configured") or []) if str(x)]
        attempted = [str(x) for x in (sources.get("attempted") or []) if str(x)]
        failures = [_failure_source_id(x) for x in (sources.get("failures") or [])]
        for source_id in configured:
            source_metrics.setdefault(source_id, _init_source(source_id))["configured_runs"] += 1
        for source_id in attempted:
            source_metrics.setdefault(source_id, _init_source(source_id))["attempted_runs"] += 1
        for source_id in failures:
            if source_id:
                source_metrics.setdefault(source_id, _init_source(source_id))["failure_count"] += 1

        current_sources: dict[str, list[str]] = {}
        for signal in signals:
            fp = str(signal.get("fingerprint") or "")
            if not fp:
                continue
            ids = _source_ids(signal)
            current_sources[fp] = ids
            signal_sources[fp] = ids
            for source_id in ids:
                source_metrics.setdefault(source_id, _init_source(source_id))["collected_signal_count"] += 1

        pre_docs: list[dict[str, Any]] = []
        analysis_docs: list[dict[str, Any]] = []
        decision_docs: list[dict[str, Any]] = []
        handoff_docs: list[dict[str, Any]] = []
        trial_docs: list[dict[str, Any]] = []
        adoption_docs: list[dict[str, Any]] = []
        for blob in blobs:
            pre_docs.extend(extract_all(blob, PREANALYSIS_START, PREANALYSIS_END))
            analysis_docs.extend(extract_all(blob, ANALYSIS_START, ANALYSIS_END))
            decision_docs.extend(extract_all(blob, DECISION_START, DECISION_END))
            handoff_docs.extend(extract_all(blob, TRIAL_HANDOFF_START, TRIAL_HANDOFF_END))
            trial_docs.extend(extract_all(blob, TRIAL_START, TRIAL_END))
            adoption_docs.extend(extract_all(blob, ADOPTION_START, ADOPTION_END))

        if pre_docs:
            queue = (pre_docs[-1].get("review_queue") or {})
            shortlist = [str(x) for x in (queue.get("shortlist_signal_fingerprints") or [])]
            semantic = [str(x) for x in (queue.get("semantic_signal_fingerprints") or [])]
            shortlist_count += len(shortlist)
            semantic_signal_count += len(semantic)
            for fp in shortlist:
                _add_for_signal(source_metrics, current_sources, fp, "shortlist_signal_count")
            for fp in semantic:
                _add_for_signal(source_metrics, current_sources, fp, "semantic_signal_count")

        latest_states: dict[str, str] = {}
        for doc in analysis_docs:
            for rec in doc.get("recommendations") or []:
                if not isinstance(rec, dict):
                    continue
                fp = str(rec.get("signal_fingerprint") or "")
                state = str(rec.get("state") or "")
                if fp and state in semantic_state_counts:
                    latest_states[fp] = state
        if not latest_states:
            for rec in evidence.get("recommendations") or []:
                if isinstance(rec, dict):
                    fp = str(rec.get("signal_fingerprint") or "")
                    state = str(rec.get("state") or "")
                    if fp and state in semantic_state_counts:
                        latest_states[fp] = state
        actionable_states = set((config.get("metrics") or {}).get("actionable_states") or [])
        for fp, state in latest_states.items():
            semantic_state_counts[state] += 1
            if state in actionable_states:
                _add_for_signal(source_metrics, current_sources, fp, "actionable_recommendation_count")

        for doc in decision_docs:
            fingerprint = str(doc.get("decision_fingerprint") or "")
            decision = doc.get("decision") or {}
            state = str(decision.get("decision") or "")
            signal_fp = str(decision.get("signal_fingerprint") or "")
            if not fingerprint or fingerprint in seen_decisions or state not in decision_counts:
                continue
            seen_decisions.add(fingerprint)
            decision_counts[state] += 1
            if state == "TRIAL":
                _add_for_signal(source_metrics, signal_sources, signal_fp, "trial_decision_count")

        for doc in handoff_docs:
            fingerprint = str(doc.get("handoff_fingerprint") or "")
            if fingerprint and fingerprint not in seen_handoffs:
                seen_handoffs.add(fingerprint)
                trial_handoff_count += 1

        for doc in trial_docs:
            fingerprint = str(doc.get("trial_fingerprint") or "")
            trial = doc.get("trial") or {}
            result = doc.get("result") or {}
            status = str(result.get("status") or "")
            signal_fp = str(trial.get("signal_fingerprint") or "")
            if not fingerprint or fingerprint in seen_trials or status not in trial_status_counts:
                continue
            seen_trials.add(fingerprint)
            trial_status_counts[status] += 1
            if status == "PASS":
                _add_for_signal(source_metrics, signal_sources, signal_fp, "trial_pass_count")

        for doc in adoption_docs:
            fingerprint = str(doc.get("adoption_fingerprint") or "")
            adoption = doc.get("adoption") or {}
            signal_fp = str(adoption.get("signal_fingerprint") or "")
            if not fingerprint or fingerprint in seen_adoptions:
                continue
            seen_adoptions.add(fingerprint)
            adoption_count += 1
            _add_for_signal(source_metrics, signal_sources, signal_fp, "adoption_count")

    duplicate_count = max(raw_signal_count - unique_signal_count, 0)
    actionable_count = sum(semantic_state_counts[state] for state in ("ASSESS", "TRIAL", "ADOPT"))
    flags_cfg = config["review_flags"]
    source_rows: list[dict[str, Any]] = []
    source_review_flags: list[dict[str, Any]] = []

    for source_id in sorted(source_metrics):
        row = source_metrics[source_id]
        ratios = {
            "shortlist_yield_basis_points": _bp(row["shortlist_signal_count"], row["collected_signal_count"]),
            "semantic_yield_basis_points": _bp(row["semantic_signal_count"], row["collected_signal_count"]),
            "actionable_from_semantic_basis_points": _bp(row["actionable_recommendation_count"], row["semantic_signal_count"]),
            "trial_from_actionable_basis_points": _bp(row["trial_decision_count"], row["actionable_recommendation_count"]),
            "adoption_from_trial_pass_basis_points": _bp(row["adoption_count"], row["trial_pass_count"]),
            "failure_rate_basis_points": _bp(row["failure_count"], row["attempted_runs"]),
        }
        flags: list[str] = []
        if row["attempted_runs"] >= flags_cfg["minimum_source_runs"]:
            failure_bp = ratios["failure_rate_basis_points"]
            if failure_bp is not None and failure_bp >= flags_cfg["high_failure_rate_basis_points_above"]:
                flags.append("REVIEW_HIGH_FAILURE_RATE")
        if row["collected_signal_count"] >= flags_cfg["minimum_source_signals"]:
            shortlist_bp = ratios["shortlist_yield_basis_points"]
            if shortlist_bp is not None and shortlist_bp < flags_cfg["low_shortlist_yield_basis_points_below"]:
                flags.append("REVIEW_LOW_SHORTLIST_YIELD")
        if (
            row["semantic_signal_count"] >= flags_cfg["zero_actionable_semantic_minimum"]
            and row["actionable_recommendation_count"] == 0
        ):
            flags.append("REVIEW_ZERO_ACTIONABLE_AFTER_SEMANTIC")
        enriched = {**row, "ratios": ratios, "review_flags": flags}
        source_rows.append(enriched)
        if flags:
            source_review_flags.append({"source_id": source_id, "flags": flags})

    report = {
        "version": 1,
        "run": {
            "mode": "monthly_effectiveness",
            "period": period,
            "generated_at": generated_at,
            "repository_revision": repository_revision,
        },
        "baseline": {
            "cohort_issue_count": len(cohort),
            "cohort_issue_numbers": [_issue_number(issue) for issue, _ in cohort],
            "input_manifest": input_manifest,
            "input_digest": canonical_digest(input_manifest),
        },
        "summary": {
            "raw_signal_count": raw_signal_count,
            "unique_signal_count": unique_signal_count,
            "duplicate_count": duplicate_count,
            "duplicate_rate_basis_points": _bp(duplicate_count, raw_signal_count),
            "shortlist_count": shortlist_count,
            "semantic_signal_count": semantic_signal_count,
            "actionable_recommendation_count": actionable_count,
            "semantic_state_counts": semantic_state_counts,
            "human_decision_counts": decision_counts,
            "trial_handoff_ready_count": trial_handoff_count,
            "trial_status_counts": trial_status_counts,
            "adoption_count": adoption_count,
        },
        "sources": source_rows,
        "review_flags": source_review_flags,
        "authority": dict(config["authority"]),
    }
    report["effectiveness_fingerprint"] = canonical_digest({
        "period": period,
        "baseline": report["baseline"],
        "summary": report["summary"],
        "sources": report["sources"],
        "review_flags": report["review_flags"],
        "authority": report["authority"],
    })
    return report


def validate_report(doc: dict[str, Any], config: dict[str, Any]) -> list[str]:
    errors = validate_config(config)
    if doc.get("version") != 1:
        errors.append("effectiveness report version must be 1")
    run = doc.get("run") or {}
    if run.get("mode") != "monthly_effectiveness":
        errors.append("effectiveness run.mode must be monthly_effectiveness")
    period = str(run.get("period") or "")
    if len(period) != 7 or period[4] != "-":
        errors.append("effectiveness period must be YYYY-MM")
    summary = doc.get("summary") or {}
    if int(summary.get("duplicate_count") or 0) != max(
        int(summary.get("raw_signal_count") or 0) - int(summary.get("unique_signal_count") or 0), 0
    ):
        errors.append("duplicate_count must equal raw minus unique signals")
    for row in doc.get("sources") or []:
        if not isinstance(row, dict) or not str(row.get("source_id") or ""):
            errors.append("each source effectiveness row requires source_id")
        flags = row.get("review_flags")
        if not isinstance(flags, list):
            errors.append("source review_flags must be a list")
    authority = doc.get("authority") or {}
    for key in (
        "automatic_source_weight_changes",
        "automatic_source_enable_disable",
        "automatic_config_mutation",
        "code_change_authorized",
        "branch_or_pr_authorized",
        "merge_authorized",
        "release_authorized",
    ):
        if authority.get(key) is not False:
            errors.append(f"effectiveness authority.{key} must be false")
    if authority.get("human_review_required_for_source_changes") is not True:
        errors.append("effectiveness source changes must remain Human-reviewed")
    expected = canonical_digest({
        "period": run.get("period"),
        "baseline": doc.get("baseline") or {},
        "summary": summary,
        "sources": doc.get("sources") or [],
        "review_flags": doc.get("review_flags") or [],
        "authority": authority,
    })
    if doc.get("effectiveness_fingerprint") != expected:
        errors.append("effectiveness_fingerprint mismatch")
    return errors


def markdown(doc: dict[str, Any]) -> str:
    summary = doc.get("summary") or {}
    lines = [
        f"## Evolution Effectiveness — {((doc.get('run') or {}).get('period') or '')}",
        "",
        "Deterministic research-effectiveness evidence only. Metrics and review flags do not mutate source policy.",
        "",
        f"- Weekly cohort Issues: {(doc.get('baseline') or {}).get('cohort_issue_count', 0)}",
        f"- Raw / unique signal observations: {summary.get('raw_signal_count', 0)} / {summary.get('unique_signal_count', 0)}",
        f"- Shortlist / semantic / actionable: {summary.get('shortlist_count', 0)} / {summary.get('semantic_signal_count', 0)} / {summary.get('actionable_recommendation_count', 0)}",
        f"- Trial handoffs ready: {summary.get('trial_handoff_ready_count', 0)}",
        f"- Trial PASS / FAIL / BLOCKED: {(summary.get('trial_status_counts') or {}).get('PASS', 0)} / {(summary.get('trial_status_counts') or {}).get('FAIL', 0)} / {(summary.get('trial_status_counts') or {}).get('BLOCKED', 0)}",
        f"- Adoption bindings: {summary.get('adoption_count', 0)}",
        f"- Sources flagged for Human review: {len(doc.get('review_flags') or [])}",
        "",
        "### Source effectiveness",
        "",
        "| Source | Collected | Shortlist | Semantic | Actionable | Trial | PASS | Adopt | Failure | Review |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in doc.get("sources") or []:
        flags = ", ".join(row.get("review_flags") or []) or "—"
        lines.append(
            f"| {row.get('source_id')} | {row.get('collected_signal_count', 0)} | "
            f"{row.get('shortlist_signal_count', 0)} | {row.get('semantic_signal_count', 0)} | "
            f"{row.get('actionable_recommendation_count', 0)} | {row.get('trial_decision_count', 0)} | "
            f"{row.get('trial_pass_count', 0)} | {row.get('adoption_count', 0)} | "
            f"{row.get('failure_count', 0)} | {flags} |"
        )
    lines += [
        "",
        "Review flags are evidence for Human source-policy review only. AIPS does not automatically reweight, enable, disable, or replace a source.",
        "",
        EFFECTIVENESS_START,
        "```yaml",
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).rstrip(),
        "```",
        EFFECTIVENESS_END,
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("--issues-json", required=True)
    build.add_argument("--config", required=True)
    build.add_argument("--period", required=True)
    build.add_argument("--repository-revision", required=True)
    build.add_argument("--generated-at", required=True)
    build.add_argument("--output", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("report")
    validate.add_argument("--config", required=True)

    render = sub.add_parser("markdown")
    render.add_argument("report")
    render.add_argument("--config", required=True)
    render.add_argument("--output", required=True)

    args = parser.parse_args()
    config = load_mapping(args.config)

    if args.command == "build":
        raw = json.loads(Path(args.issues_json).read_text(encoding="utf-8"))
        doc = build_report(
            raw,
            config,
            period=args.period,
            repository_revision=args.repository_revision,
            generated_at=args.generated_at,
        )
        errors = validate_report(doc, config)
        if errors:
            raise ValueError("generated invalid effectiveness report: " + "; ".join(errors))
        Path(args.output).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return 0

    doc = load_mapping(args.report)
    errors = validate_report(doc, config)
    if args.command == "validate":
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1
    if errors:
        raise ValueError("invalid effectiveness report: " + "; ".join(errors))
    Path(args.output).write_text(markdown(doc), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
