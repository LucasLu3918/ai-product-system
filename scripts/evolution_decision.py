#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

import yaml

from evolution_analysis import canonical_digest, extract_analysis, apply_analysis, validate_analysis
from evolution_radar import validate_evidence
from evolution_radar_rollup import extract_evidence

DECISION_START = "<!-- AIPS_EVOLUTION_DECISION_START -->"
DECISION_END = "<!-- AIPS_EVOLUTION_DECISION_END -->"
ALLOWED = {"REJECT", "HOLD", "ASSESS", "TRIAL", "ADOPT"}
PROGRESS = {"ASSESS", "TRIAL", "ADOPT"}


def candidate_id(fingerprint: str) -> str:
    return "EVO-" + fingerprint.split(":", 1)[-1][:12].upper()


def parse_approved_paths(raw: str | list[str] | None) -> list[str]:
    if raw is None:
        return []
    values = raw if isinstance(raw, list) else re.split(r"[,\n]", raw)
    result: list[str] = []
    for value in values:
        path = str(value).strip().replace("\\", "/")
        if not path:
            continue
        if path.startswith("/") or re.match(r"^[A-Za-z]:/", path):
            raise ValueError("approved paths must be repository-relative")
        if any(part == ".." for part in path.split("/")):
            raise ValueError("approved paths must not escape the repository")
        if len(path) > 240:
            raise ValueError("approved path is too long")
        if path not in result:
            result.append(path)
    if len(result) > 24:
        raise ValueError("approved paths are limited to 24 patterns")
    return result


def resolve_issue_evidence(issue: dict[str, Any]) -> dict[str, Any]:
    evidence = extract_evidence(str(issue.get("body") or ""))
    if evidence is None:
        raise ValueError("issue does not contain valid Evolution Radar evidence")
    valid: list[dict[str, Any]] = []
    for comment in issue.get("comments") or []:
        analysis = extract_analysis(str((comment or {}).get("body") or "")) if isinstance(comment, dict) else None
        if analysis is not None and not validate_analysis(evidence, analysis):
            valid.append(analysis)
    return apply_analysis(evidence, valid[-1]) if valid else evidence


def create_decision(
    evidence: dict[str, Any],
    *,
    signal_fingerprint: str,
    decision: str,
    approved_scope: str,
    approved_paths: str | list[str] | None = None,
    reason: str,
    decided_by: str,
    decided_at: str,
    current_revision: str,
) -> dict[str, Any]:
    errors = validate_evidence(evidence)
    if errors:
        raise ValueError("invalid evidence: " + "; ".join(errors))

    decision = decision.upper().strip()
    if decision not in ALLOWED:
        raise ValueError("invalid decision")
    if not reason.strip() or not decided_by.strip() or not decided_at.strip():
        raise ValueError("reason, decided_by and decided_at are required")
    if decision in {"TRIAL", "ADOPT"} and not approved_scope.strip():
        raise ValueError("TRIAL and ADOPT require approved_scope")

    path_patterns = parse_approved_paths(approved_paths)
    if decision == "TRIAL" and not path_patterns:
        raise ValueError("TRIAL requires at least one approved path pattern")

    recommendations = [
        item for item in evidence.get("recommendations") or []
        if item.get("signal_fingerprint") == signal_fingerprint
    ]
    signals = [
        item for item in evidence.get("signals") or []
        if item.get("fingerprint") == signal_fingerprint
    ]
    if len(recommendations) != 1 or len(signals) != 1:
        raise ValueError("signal fingerprint must resolve exactly once")

    base = str((evidence.get("run") or {}).get("repository_revision") or "")
    baseline_status = "CURRENT" if base and base == current_revision else "STALE"
    if decision in PROGRESS and baseline_status != "CURRENT":
        raise ValueError("progression decision blocked: Radar evidence baseline is STALE")

    recommendation_state = str(recommendations[0].get("state") or "")
    expected = {
        "ASSESS": {"ANALYSIS_PENDING", "ASSESS", "TRIAL", "ADOPT"},
        "TRIAL": {"TRIAL", "ADOPT"},
        "ADOPT": {"ADOPT"},
    }
    override = False
    if decision in PROGRESS and recommendation_state not in expected[decision]:
        if not reason.strip().lower().startswith("override:"):
            raise ValueError(
                f"{decision} exceeds advisory recommendation {recommendation_state}; "
                "prefix reason with 'override:'"
            )
        override = True

    analyzer = (evidence.get("run") or {}).get("analyzer") or {}
    if decision in {"TRIAL", "ADOPT"} and analyzer.get("status") != "available" and not override:
        raise ValueError(f"{decision} requires semantic analysis or explicit Human override")

    core = {
        "candidate_id": candidate_id(signal_fingerprint),
        "signal_fingerprint": signal_fingerprint,
        "signal_title": signals[0].get("title"),
        "evidence_digest": canonical_digest(evidence),
        "baseline_repository_revision": base,
        "baseline_status": baseline_status,
        "recommendation_state": recommendation_state,
        "decision": decision,
        "approved_scope": approved_scope.strip(),
        "approved_paths": path_patterns,
        "reason": reason.strip(),
        "human_override": override,
        "decided_by": decided_by.strip(),
        "decided_at": decided_at.strip(),
        "next_action": {
            "REJECT": "close_candidate",
            "HOLD": "continue_monitoring",
            "ASSESS": "system_improvement_review",
            "TRIAL": "controlled_trial_execution",
            "ADOPT": "system_improvement_review",
        }[decision],
    }
    return {
        "version": 1,
        "decision": core,
        "decision_fingerprint": canonical_digest(core),
        "authority": {
            "human_decision_recorded": True,
            "code_change_authorized": False,
            "branch_or_pr_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "normal_system_gates_required": decision in PROGRESS,
        },
    }


def validate_decision(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    decision = doc.get("decision") or {}
    if doc.get("version") != 1:
        errors.append("version must be 1")
    if decision.get("decision") not in ALLOWED:
        errors.append("invalid decision")
    if doc.get("decision_fingerprint") != canonical_digest(decision):
        errors.append("decision_fingerprint mismatch")
    try:
        paths = parse_approved_paths(decision.get("approved_paths") or [])
    except ValueError as exc:
        errors.append(str(exc))
        paths = []
    if decision.get("decision") == "TRIAL" and not paths:
        errors.append("TRIAL requires approved_paths")
    if decision.get("decision") in {"TRIAL", "ADOPT"} and not str(decision.get("approved_scope") or "").strip():
        errors.append("TRIAL and ADOPT require approved_scope")

    authority = doc.get("authority") or {}
    for key in ("code_change_authorized", "branch_or_pr_authorized", "merge_authorized", "release_authorized"):
        if authority.get(key) is not False:
            errors.append(f"authority.{key} must be false")
    return errors


def extract_decision(text: str) -> dict[str, Any] | None:
    if DECISION_START not in text or DECISION_END not in text:
        return None
    payload = text.split(DECISION_START, 1)[1].split(DECISION_END, 1)[0].strip()
    if payload.startswith("```yaml"):
        payload = payload[len("```yaml"):].strip()
    if payload.endswith("```"):
        payload = payload[:-3].strip()
    try:
        doc = yaml.safe_load(payload) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(doc, dict) or validate_decision(doc):
        return None
    return doc


def markdown(doc: dict[str, Any]) -> str:
    decision = doc["decision"]
    paths = decision.get("approved_paths") or []
    lines = [
        f"## Human Decision — {decision['candidate_id']}",
        "",
        f"- Signal: **{decision['signal_title']}**",
        f"- Advisory recommendation: `{decision['recommendation_state']}`",
        f"- Human decision: `{decision['decision']}`",
        f"- Baseline: `{decision['baseline_status']}` @ `{decision['baseline_repository_revision']}`",
        f"- Next action: `{decision['next_action']}`",
        "",
        f"**Reason:** {decision['reason']}",
        "",
    ]
    if decision.get("approved_scope"):
        lines += [f"**Approved scope:** {decision['approved_scope']}", ""]
    if paths:
        lines += ["**Approved trial paths:**", ""]
        lines += [f"- `{path}`" for path in paths]
        lines.append("")
    lines += [
        "This records Human direction and a bounded trial scope only; it grants no remote publication authority.",
        "",
        DECISION_START,
        "```yaml",
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).rstrip(),
        "```",
        DECISION_END,
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--issue-json", required=True)
    create.add_argument("--signal-fingerprint", required=True)
    create.add_argument("--decision", required=True)
    create.add_argument("--approved-scope", default="")
    create.add_argument("--approved-paths", default="")
    create.add_argument("--reason", required=True)
    create.add_argument("--decided-by", required=True)
    create.add_argument("--decided-at", required=True)
    create.add_argument("--current-revision", required=True)
    create.add_argument("--output", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("decision_file")

    render = sub.add_parser("markdown")
    render.add_argument("decision_file")
    render.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "create":
        issue = json.loads(Path(args.issue_json).read_text(encoding="utf-8"))
        doc = create_decision(
            resolve_issue_evidence(issue),
            signal_fingerprint=args.signal_fingerprint,
            decision=args.decision,
            approved_scope=args.approved_scope or "",
            approved_paths=args.approved_paths or "",
            reason=args.reason,
            decided_by=args.decided_by,
            decided_at=args.decided_at,
            current_revision=args.current_revision,
        )
        Path(args.output).write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return 0

    doc = yaml.safe_load(Path(args.decision_file).read_text(encoding="utf-8")) or {}
    errors = validate_decision(doc)
    if args.command == "validate":
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1
    if errors:
        raise ValueError("invalid decision: " + "; ".join(errors))
    Path(args.output).write_text(markdown(doc), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
