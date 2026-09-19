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


def validate_current_baseline(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("version") != 1:
        errors.append("current-baseline adoption evidence version must be 1")
    baseline = doc.get("baseline") or {}
    revision = str(baseline.get("repository_revision") or "")
    if len(revision) != 40 or any(ch not in "0123456789abcdef" for ch in revision.lower()):
        errors.append("current-baseline repository_revision must be a 40-character git SHA")
    if doc.get("current_state") != "TRIAL_PASS":
        errors.append("current-baseline state must be TRIAL_PASS")
    trial = doc.get("trial") or {}
    if trial.get("status") != "PASS":
        errors.append("current-baseline trial.status must be PASS")
    if trial.get("recommendation") not in {"HUMAN_REVIEW_TRIAL_RESULT", "HUMAN_REVIEW_TRIAL_EVIDENCE"}:
        errors.append("current-baseline trial recommendation must stop at Human review")
    for key in ("decision_fingerprint", "trial_fingerprint"):
        if not str(trial.get(key) or "").startswith("sha256:"):
            errors.append(f"current-baseline trial.{key} must be sha256")
    if trial.get("live_capture_verified") is not False:
        errors.append("current-baseline live_capture_verified must remain false")
    if trial.get("runtime_enforced") is not False:
        errors.append("current-baseline runtime_enforced must remain false")
    if trial.get("automatic_remediation") is not False:
        errors.append("current-baseline automatic_remediation must remain false")
    authority = doc.get("authority") or {}
    for key in (
        "human_decision_recorded",
        "adoption_authorized",
        "code_change_authorized",
        "live_runtime_capture_authorized",
        "runtime_enforcement_authorized",
        "automatic_remediation_authorized",
        "merge_authorized",
        "release_authorized",
        "publication_authorized",
    ):
        if authority.get(key) is not False:
            errors.append(f"current-baseline authority.{key} must be false")
    return errors


def bind_committed(
    baseline_doc: dict[str, Any],
    trial_decision_doc: dict[str, Any],
    trial_result_doc: dict[str, Any],
    adopt_decision_doc: dict[str, Any],
) -> dict[str, Any]:
    baseline_errors = validate_current_baseline(baseline_doc)
    if baseline_errors:
        raise ValueError("invalid current-baseline adoption evidence: " + "; ".join(baseline_errors))

    trial_decision_errors = validate_decision(trial_decision_doc)
    if trial_decision_errors:
        raise ValueError("invalid TRIAL decision: " + "; ".join(trial_decision_errors))
    adopt_decision_errors = validate_decision(adopt_decision_doc)
    if adopt_decision_errors:
        raise ValueError("invalid ADOPT decision: " + "; ".join(adopt_decision_errors))

    trial_decision = trial_decision_doc.get("decision") or {}
    adopt_decision = adopt_decision_doc.get("decision") or {}
    if trial_decision.get("decision") != "TRIAL":
        raise ValueError("committed adoption binding requires the prior Human Decision to be TRIAL")
    if adopt_decision.get("decision") != "ADOPT":
        raise ValueError("committed adoption binding requires an ADOPT Human Decision")
    if adopt_decision.get("baseline_status") != "CURRENT":
        raise ValueError("ADOPT Human Decision must be CURRENT")
    if adopt_decision.get("human_override") is not True:
        raise ValueError("TRIAL PASS to ADOPT direction requires an explicit Human override")

    baseline = baseline_doc.get("baseline") or {}
    trial_baseline = baseline_doc.get("trial") or {}
    current_revision = str(baseline.get("repository_revision") or "")
    if adopt_decision.get("baseline_repository_revision") != current_revision:
        raise ValueError("ADOPT decision baseline does not match current-baseline evidence")
    if adopt_decision.get("evidence_digest") != canonical_digest(baseline_doc):
        raise ValueError("ADOPT decision evidence_digest does not match current-baseline evidence")

    for key in ("candidate_id", "signal_fingerprint"):
        if trial_decision.get(key) != adopt_decision.get(key):
            raise ValueError(f"TRIAL and ADOPT decisions disagree on {key}")
    if baseline.get("signal_fingerprint") != adopt_decision.get("signal_fingerprint"):
        raise ValueError("current-baseline signal does not match ADOPT decision")

    if trial_baseline.get("decision_fingerprint") != trial_decision_doc.get("decision_fingerprint"):
        raise ValueError("current-baseline Trial Decision fingerprint mismatch")
    if trial_result_doc.get("decision_fingerprint") != trial_decision_doc.get("decision_fingerprint"):
        raise ValueError("committed Trial result does not bind the prior Human Decision")
    if trial_result_doc.get("baseline_repository_revision") != trial_decision.get("baseline_repository_revision"):
        raise ValueError("committed Trial result baseline does not match prior Human Decision")
    if trial_result_doc.get("status") != "PASS":
        raise ValueError("committed adoption binding requires a PASS Trial result")
    if trial_result_doc.get("recommendation") not in {"HUMAN_REVIEW_TRIAL_RESULT", "HUMAN_REVIEW_TRIAL_EVIDENCE"}:
        raise ValueError("committed Trial result must stop at Human review")
    fingerprint = str(trial_result_doc.get("trial_fingerprint") or "")
    if not fingerprint.startswith("sha256:"):
        raise ValueError("committed Trial result fingerprint must be sha256")
    if trial_baseline.get("trial_fingerprint") != fingerprint:
        raise ValueError("current-baseline Trial fingerprint does not match committed Trial result")

    trial_authority = trial_result_doc.get("authority") or {}
    if trial_authority.get("human_adoption_decision_required") is not True:
        raise ValueError("committed Trial result must require a Human adoption decision")
    for key in (
        "live_runtime_capture_authorized",
        "runtime_enforcement_authorized",
        "automatic_remediation_authorized",
        "human_approval_granted",
        "merge_authorized",
        "release_authorized",
        "publication_authorized",
    ):
        if trial_authority.get(key) is not False:
            raise ValueError(f"committed Trial result must keep authority.{key}=false")

    core = {
        "candidate_id": adopt_decision["candidate_id"],
        "signal_fingerprint": adopt_decision["signal_fingerprint"],
        "decision_fingerprint": adopt_decision_doc["decision_fingerprint"],
        "trial_decision_fingerprint": trial_decision_doc["decision_fingerprint"],
        "trial_fingerprint": fingerprint,
        "baseline_repository_revision": current_revision,
        "trial_baseline_repository_revision": trial_decision["baseline_repository_revision"],
        "baseline_evidence_digest": canonical_digest(baseline_doc),
        "binding_mode": "COMMITTED_CURRENT_BASELINE_TRIAL",
        "trial_status": "PASS",
        "decided_by": adopt_decision["decided_by"],
        "decided_at": adopt_decision["decided_at"],
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
    binding_mode = adoption.get("binding_mode")
    if binding_mode is not None and binding_mode not in {"COMMITTED_CURRENT_BASELINE_TRIAL"}:
        errors.append("unsupported adoption binding_mode")
    if binding_mode == "COMMITTED_CURRENT_BASELINE_TRIAL":
        for key in (
            "trial_decision_fingerprint",
            "trial_baseline_repository_revision",
            "baseline_evidence_digest",
        ):
            if not str(adoption.get(key) or "").strip():
                errors.append(f"committed adoption binding missing {key}")
        if adoption.get("baseline_repository_revision") == adoption.get("trial_baseline_repository_revision"):
            errors.append("committed adoption binding must distinguish current baseline from Trial baseline")
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
        *(
            [
                f"- Binding mode: {adoption['binding_mode']}",
                f"- Trial baseline: {adoption['trial_baseline_repository_revision']}",
            ]
            if adoption.get("binding_mode")
            else []
        ),
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

    committed = sub.add_parser("bind-committed")
    committed.add_argument("--baseline", required=True)
    committed.add_argument("--trial-decision", required=True)
    committed.add_argument("--trial-result", required=True)
    committed.add_argument("--adopt-decision", required=True)
    committed.add_argument("--output", required=True)

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

    if args.command == "bind-committed":
        baseline_doc = yaml.safe_load(Path(args.baseline).read_text(encoding="utf-8")) or {}
        trial_decision_doc = yaml.safe_load(Path(args.trial_decision).read_text(encoding="utf-8")) or {}
        trial_result_doc = yaml.safe_load(Path(args.trial_result).read_text(encoding="utf-8")) or {}
        adopt_decision_doc = yaml.safe_load(Path(args.adopt_decision).read_text(encoding="utf-8")) or {}
        doc = bind_committed(baseline_doc, trial_decision_doc, trial_result_doc, adopt_decision_doc)
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
