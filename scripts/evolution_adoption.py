#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from evolution_analysis import canonical_digest
from evolution_decision import validate_decision
from evolution_trial import validate_result

TRIAL_START = "<!-- AIPS_EVOLUTION_TRIAL_START -->"
TRIAL_END = "<!-- AIPS_EVOLUTION_TRIAL_END -->"
ADOPTION_START = "<!-- AIPS_EVOLUTION_ADOPTION_START -->"
ADOPTION_END = "<!-- AIPS_EVOLUTION_ADOPTION_END -->"


def extract_trial(text: str) -> dict[str, Any] | None:
    if TRIAL_START not in text or TRIAL_END not in text:
        return None
    payload = text.split(TRIAL_START, 1)[1].split(TRIAL_END, 1)[0].strip()
    if payload.startswith("```yaml"):
        payload = payload[len("```yaml"):].strip()
    if payload.endswith("```"):
        payload = payload[:-3].strip()
    try:
        doc = yaml.safe_load(payload) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(doc, dict) or validate_result(doc):
        return None
    return doc


def bind(issue: dict[str, Any], decision_doc: dict[str, Any], trial_fingerprint: str) -> dict[str, Any]:
    decision_errors = validate_decision(decision_doc)
    if decision_errors:
        raise ValueError("invalid ADOPT decision: " + "; ".join(decision_errors))
    decision = decision_doc.get("decision") or {}
    if decision.get("decision") != "ADOPT":
        raise ValueError("adoption binding requires an ADOPT Human Decision")
    fingerprint = trial_fingerprint.strip()
    if not fingerprint.startswith("sha256:"):
        raise ValueError("trial_fingerprint must be sha256")

    matches: list[dict[str, Any]] = []
    for comment in issue.get("comments") or []:
        if not isinstance(comment, dict):
            continue
        trial = extract_trial(str(comment.get("body") or ""))
        if trial is not None and trial.get("trial_fingerprint") == fingerprint:
            matches.append(trial)
    if len(matches) != 1:
        raise ValueError("trial_fingerprint must resolve exactly once in the Radar Issue")

    trial_doc = matches[0]
    trial = trial_doc.get("trial") or {}
    result = trial_doc.get("result") or {}
    if result.get("status") != "PASS":
        raise ValueError("ADOPT trial binding requires a PASS Trial Report")
    if trial.get("candidate_id") != decision.get("candidate_id"):
        raise ValueError("Trial candidate does not match ADOPT decision")
    if trial.get("signal_fingerprint") != decision.get("signal_fingerprint"):
        raise ValueError("Trial signal does not match ADOPT decision")
    if trial.get("baseline_repository_revision") != decision.get("baseline_repository_revision"):
        raise ValueError("Trial baseline does not match ADOPT decision")

    core = {
        "candidate_id": decision["candidate_id"],
        "signal_fingerprint": decision["signal_fingerprint"],
        "decision_fingerprint": decision_doc["decision_fingerprint"],
        "trial_fingerprint": fingerprint,
        "baseline_repository_revision": decision["baseline_repository_revision"],
        "trial_status": "PASS",
        "decided_by": decision["decided_by"],
        "decided_at": decision["decided_at"],
        "next_action": "system_improvement_review",
    }
    return {
        "version": 1,
        "adoption": core,
        "adoption_fingerprint": canonical_digest(core),
        "authority": {
            "code_change_authorized": False,
            "remote_branch_or_pr_authorized": False,
            "merge_authorized": False,
            "release_authorized": False,
            "normal_system_gates_required": True,
        },
    }


def validate(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("version") != 1:
        errors.append("adoption version must be 1")
    adoption = doc.get("adoption") or {}
    if adoption.get("trial_status") != "PASS":
        errors.append("adoption trial_status must be PASS")
    if adoption.get("next_action") != "system_improvement_review":
        errors.append("adoption next_action must be system_improvement_review")
    if doc.get("adoption_fingerprint") != canonical_digest(adoption):
        errors.append("adoption_fingerprint mismatch")
    authority = doc.get("authority") or {}
    for key in ("code_change_authorized", "remote_branch_or_pr_authorized", "merge_authorized", "release_authorized"):
        if authority.get(key) is not False:
            errors.append(f"authority.{key} must be false")
    if authority.get("normal_system_gates_required") is not True:
        errors.append("normal system gates must remain required")
    return errors


def markdown(doc: dict[str, Any]) -> str:
    adoption = doc["adoption"]
    return "\n".join([
        f"## Trial → ADOPT Binding — {adoption['candidate_id']}",
        "",
        f"- Trial fingerprint: {adoption['trial_fingerprint']}",
        "- Trial status: PASS",
        f"- ADOPT decision fingerprint: {adoption['decision_fingerprint']}",
        f"- Baseline: {adoption['baseline_repository_revision']}",
        "- Next action: system_improvement_review",
        "",
        "This binds Human ADOPT direction to validated Trial evidence only. It grants no code publication, PR, merge, or release authority.",
        "",
        ADOPTION_START,
        "```yaml",
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).rstrip(),
        "```",
        ADOPTION_END,
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    bind_cmd = sub.add_parser("bind")
    bind_cmd.add_argument("--issue-json", required=True)
    bind_cmd.add_argument("--decision", required=True)
    bind_cmd.add_argument("--trial-fingerprint", required=True)
    bind_cmd.add_argument("--output", required=True)

    validate_cmd = sub.add_parser("validate")
    validate_cmd.add_argument("adoption_file")

    render = sub.add_parser("markdown")
    render.add_argument("adoption_file")
    render.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "bind":
        issue = json.loads(Path(args.issue_json).read_text(encoding="utf-8"))
        decision_doc = yaml.safe_load(Path(args.decision).read_text(encoding="utf-8")) or {}
        doc = bind(issue, decision_doc, args.trial_fingerprint)
        Path(args.output).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return 0

    doc = yaml.safe_load(Path(args.adoption_file).read_text(encoding="utf-8")) or {}
    errors = validate(doc)
    if args.command == "validate":
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1
    if errors:
        raise ValueError("invalid adoption binding: " + "; ".join(errors))
    Path(args.output).write_text(markdown(doc), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
