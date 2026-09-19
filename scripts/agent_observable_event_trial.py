#!/usr/bin/env python3
"""Replay-only provider-neutral observable-event integration Trial for AIPS."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import yaml

import agent_anomaly_evaluation as anomaly
import evolution_decision


class TrialError(ValueError):
    pass


CANONICAL_REQUIRED = (
    "event_id",
    "observed_at",
    "subject",
    "resource_id",
    "operation",
    "observed_outcome",
    "network_used",
)
CANONICAL_OPTIONAL = ("change_boundary",)
REPORT_FIELD_SET = [
    "adapter_id",
    "change_boundary",
    "event_id",
    "network_used",
    "observed_at",
    "observed_outcome",
    "operation",
    "resource_id",
    "runtime",
    "subject",
]


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise TrialError(f"{path}: expected mapping")
    return value


def validate_config(config: dict[str, Any]) -> None:
    if config.get("version") != 1:
        raise TrialError("config.version must be 1")
    if config.get("mode") != "ADAPTER_EXPORT_REPLAY":
        raise TrialError("Trial mode must remain ADAPTER_EXPORT_REPLAY")
    if config.get("live_capture_verified") is not False:
        raise TrialError("live_capture_verified must remain false")
    if config.get("raw_payload_persisted") is not False:
        raise TrialError("raw_payload_persisted must remain false")
    for key in ("max_events", "max_string_length"):
        value = config.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise TrialError(f"{key} must be a positive integer")

    adapters = config.get("adapters")
    if not isinstance(adapters, dict) or not adapters:
        raise TrialError("adapters must be a non-empty mapping")
    for adapter_id, adapter in adapters.items():
        if not isinstance(adapter_id, str) or not adapter_id.strip() or not isinstance(adapter, dict):
            raise TrialError("adapter entries must be named mappings")
        field_map = adapter.get("field_map")
        outcome_map = adapter.get("outcome_map")
        if not isinstance(field_map, dict) or not isinstance(outcome_map, dict):
            raise TrialError(f"{adapter_id}: field_map/outcome_map are required")
        for field in CANONICAL_REQUIRED:
            if not str(field_map.get(field) or "").strip():
                raise TrialError(f"{adapter_id}: mapping for {field} is required")
        if any(value not in anomaly.OUTCOMES for value in outcome_map.values()):
            raise TrialError(f"{adapter_id}: outcome map may only emit canonical outcomes")

    authority = config.get("authority") or {}
    required_false = (
        "live_runtime_capture_authorized",
        "runtime_enforcement_authorized",
        "automatic_remediation_authorized",
        "human_approval_granted",
        "merge_authorized",
        "release_authorized",
        "publication_authorized",
    )
    if any(authority.get(key) is not False for key in required_false):
        raise TrialError("Trial config must not grant runtime/protected authority")


def validate_binding(
    baseline: dict[str, Any],
    decision: dict[str, Any],
    fixture: dict[str, Any],
) -> None:
    decision_errors = evolution_decision.validate_decision(decision)
    if decision_errors:
        raise TrialError("invalid Human Decision: " + "; ".join(decision_errors))
    d = decision["decision"]
    if d.get("decision") != "TRIAL":
        raise TrialError("observable-event integration requires TRIAL decision")
    if d.get("baseline_status") != "CURRENT":
        raise TrialError("TRIAL decision must have been CURRENT when recorded")
    if d.get("human_override") is not True:
        raise TrialError("ASSESS to TRIAL progression requires explicit Human override")
    if anomaly.digest(baseline) != d.get("evidence_digest"):
        raise TrialError("Human Decision evidence_digest does not match current-baseline assessment")
    revision = str((baseline.get("baseline") or {}).get("repository_revision") or "")
    if d.get("baseline_repository_revision") != revision:
        raise TrialError("Human Decision baseline does not match baseline assessment")
    if fixture.get("baseline_repository_revision") != revision:
        raise TrialError("Trial fixture baseline does not match Human Decision")
    if fixture.get("decision_fingerprint") != decision.get("decision_fingerprint"):
        raise TrialError("Trial fixture decision fingerprint is stale")
    if d.get("signal_fingerprint") != (baseline.get("baseline") or {}).get("signal_fingerprint"):
        raise TrialError("Human Decision signal does not match baseline assessment")


def _validate_timestamp(value: str, case_id: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TrialError(f"{case_id}: observed timestamp must be ISO-8601") from exc


def normalize_event(
    case: dict[str, Any],
    config: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    case_id = str(case.get("id") or "").strip()
    adapter_id = str(case.get("adapter") or "").strip()
    runtime = str(case.get("runtime") or "").strip()
    adapters = config["adapters"]
    if adapter_id not in adapters:
        raise TrialError(f"{case_id}: unknown adapter {adapter_id}")
    if not runtime:
        raise TrialError(f"{case_id}: runtime is required")

    raw = case.get("raw_event")
    if not isinstance(raw, dict):
        raise TrialError(f"{case_id}: raw_event must be a mapping")
    if anomaly.private_reasoning_paths(raw):
        raise TrialError(f"{case_id}: private reasoning fields are prohibited")
    if anomaly.secret_findings(raw):
        raise TrialError(f"{case_id}: secret-like values are prohibited")

    adapter = adapters[adapter_id]
    field_map = adapter["field_map"]
    allowed_raw = {str(value) for value in field_map.values() if str(value).strip()}
    extra = sorted(set(str(key) for key in raw) - allowed_raw)
    if extra:
        raise TrialError(f"{case_id}: unmapped raw fields are prohibited: {', '.join(extra)}")

    event: dict[str, Any] = {}
    for field in CANONICAL_REQUIRED + CANONICAL_OPTIONAL:
        source_key = str(field_map.get(field) or "").strip()
        if source_key and source_key in raw:
            event[field] = raw[source_key]

    for field in CANONICAL_REQUIRED:
        if field not in event:
            raise TrialError(f"{case_id}: missing mapped field {field}")
    if not isinstance(event["network_used"], bool):
        raise TrialError(f"{case_id}: network_used must be boolean")

    outcome = str(event["observed_outcome"])
    mapped = adapter["outcome_map"].get(outcome)
    if mapped not in anomaly.OUTCOMES:
        raise TrialError(f"{case_id}: unsupported adapter outcome {outcome}")
    event["observed_outcome"] = mapped

    max_length = int(config["max_string_length"])
    for field in (
        "event_id",
        "observed_at",
        "subject",
        "resource_id",
        "operation",
        "change_boundary",
    ):
        value = event.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise TrialError(f"{case_id}: {field} must be a non-empty string when present")
        if len(value) > max_length:
            raise TrialError(f"{case_id}: {field} exceeds max_string_length")
        event[field] = value.strip()

    _validate_timestamp(str(event["observed_at"]), case_id)
    event["runtime"] = runtime
    event["adapter_id"] = adapter_id
    return event, anomaly.digest(event)


def validate_fixture(fixture: dict[str, Any], config: dict[str, Any]) -> None:
    if fixture.get("version") != 1:
        raise TrialError("fixture.version must be 1")
    for key in ("trial_id", "baseline_repository_revision", "decision_fingerprint"):
        if not str(fixture.get(key) or "").strip():
            raise TrialError(f"fixture.{key} is required")
    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases:
        raise TrialError("fixture.cases must be a non-empty list")
    if len(cases) > int(config["max_events"]):
        raise TrialError("fixture exceeds max_events")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise TrialError("each case must be a mapping")
        case_id = str(case.get("id") or "").strip()
        if not case_id or case_id in seen:
            raise TrialError("case ids must be non-empty and unique")
        seen.add(case_id)
        if not isinstance(case.get("expected_anomaly"), bool):
            raise TrialError(f"{case_id}: expected_anomaly must be boolean")
        expected_types = case.get("expected_types") or []
        if not isinstance(expected_types, list) or not all(isinstance(x, str) and x.strip() for x in expected_types):
            raise TrialError(f"{case_id}: expected_types must contain strings")
        normalize_event(case, config)

    thresholds = fixture.get("thresholds")
    if not isinstance(thresholds, dict):
        raise TrialError("fixture.thresholds must be a mapping")
    for key in ("min_precision", "min_recall", "max_false_positive_rate", "max_false_negative_rate"):
        value = thresholds.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
            raise TrialError(f"thresholds.{key} must be between 0 and 1")


def run_trial(
    config: dict[str, Any],
    profile: dict[str, Any],
    baseline: dict[str, Any],
    decision: dict[str, Any],
    fixture: dict[str, Any],
) -> dict[str, Any]:
    validate_config(config)
    validate_binding(baseline, decision, fixture)
    validate_fixture(fixture, config)

    canonical_cases: list[dict[str, Any]] = []
    source_meta: dict[str, dict[str, str]] = {}
    for case in fixture["cases"]:
        event, fingerprint = normalize_event(case, config)
        canonical_cases.append(
            {
                "id": case["id"],
                "expected_anomaly": case["expected_anomaly"],
                "expected_types": list(case.get("expected_types") or []),
                "event": event,
            }
        )
        source_meta[str(case["id"])] = {
            "adapter": str(case["adapter"]),
            "runtime": str(case["runtime"]),
            "event_fingerprint": fingerprint,
        }

    anomaly_corpus = {
        "version": 1,
        "evaluation_id": fixture["trial_id"],
        "thresholds": fixture["thresholds"],
        "cases": canonical_cases,
    }
    evaluated = anomaly.evaluate(anomaly_corpus, profile)

    case_rows: list[dict[str, Any]] = []
    for row in evaluated["cases"]:
        meta = source_meta[str(row["id"])]
        case_rows.append(
            {
                "id": row["id"],
                "adapter": meta["adapter"],
                "runtime": meta["runtime"],
                "event_fingerprint": meta["event_fingerprint"],
                "expected_anomaly": row["expected_anomaly"],
                "detected_anomaly": row["detected_anomaly"],
                "expected_types": row["expected_types"],
                "detected_types": row["detected_types"],
                "classification_correct": row["classification_correct"],
            }
        )

    core = {
        "version": 1,
        "trial_id": fixture["trial_id"],
        "baseline_repository_revision": fixture["baseline_repository_revision"],
        "decision_fingerprint": fixture["decision_fingerprint"],
        "mode": config["mode"],
        "live_capture_verified": False,
        "raw_payload_persisted": False,
        "case_count": len(case_rows),
        "normalized_field_set": list(REPORT_FIELD_SET),
        "metrics": evaluated["metrics"],
        "thresholds": fixture["thresholds"],
        "cases": case_rows,
        "status": evaluated["status"],
        "recommendation": "HUMAN_REVIEW_TRIAL_RESULT" if evaluated["status"] == "PASS" else "HOLD",
    }
    report = dict(core)
    report["trial_fingerprint"] = anomaly.digest(core)
    report["enforcement"] = {
        "mode": "POST_EXECUTION_EVIDENCE",
        "runtime_enforced": False,
        "critical_path": False,
        "automatic_remediation": False,
    }
    report["authority"] = {
        "human_adoption_decision_required": True,
        "live_runtime_capture_authorized": False,
        "runtime_enforcement_authorized": False,
        "automatic_remediation_authorized": False,
        "human_approval_granted": False,
        "merge_authorized": False,
        "release_authorized": False,
        "publication_authorized": False,
    }
    return report


def emit(value: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "run"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--config", required=True, type=Path)
        cmd.add_argument("--profile", required=True, type=Path)
        cmd.add_argument("--baseline", required=True, type=Path)
        cmd.add_argument("--decision", required=True, type=Path)
        cmd.add_argument("--fixture", required=True, type=Path)
        if name == "run":
            cmd.add_argument("--output", type=Path)

    args = parser.parse_args()
    try:
        config_doc = load_yaml(args.config)
        profile_doc = load_yaml(args.profile)
        baseline_doc = load_yaml(args.baseline)
        decision_doc = load_yaml(args.decision)
        fixture_doc = load_yaml(args.fixture)
        validate_config(config_doc)
        validate_binding(baseline_doc, decision_doc, fixture_doc)
        validate_fixture(fixture_doc, config_doc)

        if args.command == "validate":
            result = {
                "version": 1,
                "status": "PASS",
                "trial_id": fixture_doc["trial_id"],
                "case_count": len(fixture_doc["cases"]),
                "mode": "ADAPTER_EXPORT_REPLAY",
                "live_capture_verified": False,
                "raw_payload_persisted": False,
                "decision_fingerprint": fixture_doc["decision_fingerprint"],
                "authority": config_doc["authority"],
            }
            print(emit(result, args.format), end="")
            return 0

        report = run_trial(config_doc, profile_doc, baseline_doc, decision_doc, fixture_doc)
        rendered = emit(report, args.format)
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0 if report["status"] == "PASS" else 1
    except (OSError, yaml.YAMLError, ValueError, TrialError) as exc:
        print(f"AGENT OBSERVABLE EVENT TRIAL BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
