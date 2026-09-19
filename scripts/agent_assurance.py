#!/usr/bin/env python3
"""Provider-neutral Agent Runtime Assurance evidence for AIPS."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml

from resource_authorization import OPERATIONS, canonical_hash as authorization_hash
from resource_authorization import decision as authorization_decision
from resource_authorization import validate_profile

INTENT_STATES = {"ALIGNED", "AMBIGUOUS", "MISALIGNED", "HIGH_RISK"}
OUTCOMES = {"SUCCESS", "DENIED", "FAILED"}
FORBIDDEN_KEYS = {
    "analysis", "chain_of_thought", "chain-of-thought", "cot",
    "private_reasoning", "reasoning_trace", "scratchpad", "thoughts",
}
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:password|api[_-]?key|secret|token)\s*[:=]\s*[^\s,;]{8,}"),
)


class AssuranceError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise AssuranceError(f"{path}: expected mapping")
    return data


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def private_reasoning_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).strip().lower() in FORBIDDEN_KEYS:
                found.append(path)
            found.extend(private_reasoning_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(private_reasoning_paths(child, f"{prefix}[{index}]"))
    return found


def secret_findings(value: Any, prefix: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            findings.extend(secret_findings(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(secret_findings(child, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        if any(pattern.search(value) for pattern in SECRET_PATTERNS):
            findings.append(prefix or "<root>")
    return findings


def authority() -> dict[str, bool]:
    return {
        "human_approval_granted": False,
        "tool_call_authorized": False,
        "merge_authorized": False,
        "release_authorized": False,
        "protected_operation_authorized": False,
        "automatic_remediation_authorized": False,
    }


def request_artifact(profile: dict[str, Any], resource_id: str, operation: str, change_boundary: str | None, declared_intent: str) -> dict[str, Any]:
    validate_profile(profile)
    declared_intent = declared_intent.strip()
    if not declared_intent:
        raise AssuranceError("declared_intent is required")
    if secret_findings(declared_intent):
        raise AssuranceError("declared_intent contains secret-like values")
    auth = authorization_decision(profile, resource_id, operation, change_boundary)
    request = {
        "subject": profile["subject"]["id"],
        "resource_id": resource_id,
        "operation": operation,
        "change_boundary": change_boundary,
        "declared_intent": declared_intent,
        "authorization_profile_fingerprint": authorization_hash(profile),
        "authorization_status": auth["status"],
    }
    return {
        "version": 1,
        "request": request,
        "request_fingerprint": digest(request),
        "enforcement": {"mode": "PRE_EXECUTION_EVIDENCE", "runtime_enforced": False, "semantic_provider_required_by_core": False},
        "authority": authority(),
    }


def validate_request(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("version") != 1:
        raise AssuranceError("request.version must be 1")
    request = doc.get("request")
    if not isinstance(request, dict):
        raise AssuranceError("request.request must be a mapping")
    for key in ("subject", "resource_id", "operation", "declared_intent", "authorization_profile_fingerprint", "authorization_status"):
        if not str(request.get(key) or "").strip():
            raise AssuranceError(f"request.{key} is required")
    if request["operation"] not in OPERATIONS:
        raise AssuranceError("request.operation is unsupported")
    if request["authorization_status"] not in {"ALLOW", "DENY"}:
        raise AssuranceError("request.authorization_status must be ALLOW or DENY")
    if doc.get("request_fingerprint") != digest(request):
        raise AssuranceError("request_fingerprint is missing or stale")
    if private_reasoning_paths(doc):
        raise AssuranceError("private reasoning fields are prohibited")
    if secret_findings(doc):
        raise AssuranceError("secret-like values are prohibited")
    return request


def validate_semantic_result(result: dict[str, Any], request_fingerprint: str) -> dict[str, Any]:
    if result.get("version") != 1 or result.get("request_fingerprint") != request_fingerprint:
        raise AssuranceError("semantic result binding is invalid")
    assessment = result.get("assessment")
    if not isinstance(assessment, dict) or assessment.get("state") not in INTENT_STATES:
        raise AssuranceError("assessment.state is unsupported")
    confidence = assessment.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= float(confidence) <= 1:
        raise AssuranceError("assessment.confidence must be between 0 and 1")
    for key in ("summary", "provider", "model", "assessed_at"):
        if not str(assessment.get(key) or "").strip():
            raise AssuranceError(f"assessment.{key} is required")
    evidence = assessment.get("evidence")
    if not isinstance(evidence, list) or not evidence or not all(isinstance(x, str) and x.strip() for x in evidence):
        raise AssuranceError("assessment.evidence must be a non-empty list of strings")
    if private_reasoning_paths(result):
        raise AssuranceError("private reasoning fields are prohibited")
    if secret_findings(result):
        raise AssuranceError("secret-like values are prohibited")
    supplied_authority = result.get("authority") or {}
    if not isinstance(supplied_authority, dict) or any(value is not False for value in supplied_authority.values()):
        raise AssuranceError("semantic result may not grant authority")
    return assessment


def finalize_intent(request_doc: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    request = validate_request(request_doc)
    request_fp = request_doc["request_fingerprint"]
    assessment = validate_semantic_result(result, request_fp)
    return {
        "version": 1,
        "request": request,
        "request_fingerprint": request_fp,
        "assessment": assessment,
        "assessment_fingerprint": digest({"request_fingerprint": request_fp, "assessment": assessment}),
        "enforcement": {"mode": "PRE_EXECUTION_EVIDENCE", "runtime_enforced": False, "can_only_narrow_authorization": True},
        "authority": authority(),
    }


def validate_final_assessment(doc: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if doc.get("version") != 1:
        raise AssuranceError("assessment artifact.version must be 1")
    request = doc.get("request")
    assessment = doc.get("assessment")
    if not isinstance(request, dict) or not isinstance(assessment, dict):
        raise AssuranceError("assessment artifact requires request and assessment")
    request_fp = doc.get("request_fingerprint")
    if request_fp != digest(request):
        raise AssuranceError("assessment request fingerprint is stale")
    validate_semantic_result({"version": 1, "request_fingerprint": request_fp, "assessment": assessment, "authority": authority()}, request_fp)
    if doc.get("assessment_fingerprint") != digest({"request_fingerprint": request_fp, "assessment": assessment}):
        raise AssuranceError("assessment_fingerprint is missing or stale")
    return request, assessment


def intent_gate(profile: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    validate_profile(profile)
    request, assessment = validate_final_assessment(artifact)
    if request.get("subject") != profile["subject"]["id"]:
        raise AssuranceError("assessment subject does not match profile")
    if request.get("authorization_profile_fingerprint") != authorization_hash(profile):
        raise AssuranceError("authorization profile fingerprint is stale")
    auth = authorization_decision(profile, str(request["resource_id"]), str(request["operation"]), request.get("change_boundary"))
    if auth["status"] != request.get("authorization_status"):
        raise AssuranceError("authorization status no longer matches profile")
    if auth["status"] != "ALLOW":
        status, reason = "BLOCKED", "resource_authorization_denied"
    elif assessment["state"] != "ALIGNED":
        status, reason = "BLOCKED", "intent_" + str(assessment["state"]).lower()
    else:
        status, reason = "COMPATIBLE", "authorization_and_intent_evidence_aligned"
    return {
        "version": 1,
        "status": status,
        "reason": reason,
        "resource_authorization_status": auth["status"],
        "intent_state": assessment["state"],
        "request_fingerprint": artifact["request_fingerprint"],
        "assessment_fingerprint": artifact["assessment_fingerprint"],
        "enforcement": {"mode": "PRE_EXECUTION_EVIDENCE", "runtime_enforced": False, "can_only_narrow_authorization": True},
        "authority": authority(),
    }


def validate_events(doc: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    if doc.get("version") != 1:
        raise AssuranceError("events.version must be 1")
    subject = str(doc.get("subject") or "").strip()
    events = doc.get("events")
    if not subject or not isinstance(events, list) or not events:
        raise AssuranceError("events require subject and non-empty events")
    seen: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            raise AssuranceError("each event must be a mapping")
        event_id = str(event.get("id") or "").strip()
        if not event_id or event_id in seen:
            raise AssuranceError("event ids must be non-empty and unique")
        seen.add(event_id)
        for key in ("resource_id", "operation", "observed_outcome"):
            if not str(event.get(key) or "").strip():
                raise AssuranceError(f"event {event_id}: {key} is required")
        if event["observed_outcome"] not in OUTCOMES:
            raise AssuranceError(f"event {event_id}: unsupported outcome")
        if "network_used" in event and not isinstance(event["network_used"], bool):
            raise AssuranceError(f"event {event_id}: network_used must be boolean")
    if private_reasoning_paths(doc):
        raise AssuranceError("private reasoning fields are prohibited")
    if secret_findings(doc):
        raise AssuranceError("secret-like values are prohibited")
    return subject, events


def postflight(profile: dict[str, Any], events_doc: dict[str, Any]) -> dict[str, Any]:
    validate_profile(profile)
    subject, events = validate_events(events_doc)
    anomalies: list[dict[str, Any]] = []
    expected_denials = 0
    for event in events:
        event_id = str(event["id"])
        if subject != profile["subject"]["id"]:
            anomalies.append({"event_id": event_id, "type": "subject_mismatch", "severity": "HIGH"})
            continue
        operation = str(event["operation"])
        if operation not in OPERATIONS:
            anomalies.append({"event_id": event_id, "type": "unsupported_operation_observed", "severity": "HIGH"})
            continue
        auth = authorization_decision(profile, str(event["resource_id"]), operation, event.get("change_boundary"))
        if auth["status"] == "DENY":
            if event["observed_outcome"] == "SUCCESS":
                anomalies.append({"event_id": event_id, "type": "unauthorized_success", "severity": "HIGH"})
            else:
                expected_denials += 1
        grant = next((g for g in profile["grants"] if g["id"] == event["resource_id"]), None)
        if grant is not None and event.get("network_used", False) and (grant.get("constraints") or {}).get("network_allowed") is False:
            anomalies.append({"event_id": event_id, "type": "network_policy_violation", "severity": "HIGH"})
    return {
        "version": 1,
        "status": "REVIEW" if anomalies else "PASS",
        "subject": subject,
        "authorization_profile_fingerprint": authorization_hash(profile),
        "events_fingerprint": digest(events_doc),
        "summary": {"events": len(events), "anomalies": len(anomalies), "expected_denials": expected_denials},
        "anomalies": anomalies,
        "enforcement": {"mode": "POST_EXECUTION_EVIDENCE", "runtime_enforced": False, "critical_path": False, "automatic_remediation": False},
        "authority": authority(),
    }


def emit(doc: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(doc, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).rstrip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    req = sub.add_parser("intent-request")
    req.add_argument("--profile", required=True, type=Path)
    req.add_argument("--resource-id", required=True)
    req.add_argument("--operation", required=True, choices=sorted(OPERATIONS))
    req.add_argument("--change-boundary")
    req.add_argument("--declared-intent", required=True)
    req.add_argument("--format", choices=("yaml", "json"), default="yaml")
    fin = sub.add_parser("intent-finalize")
    fin.add_argument("--request", required=True, type=Path)
    fin.add_argument("--result", required=True, type=Path)
    fin.add_argument("--format", choices=("yaml", "json"), default="yaml")
    gate = sub.add_parser("intent-gate")
    gate.add_argument("--profile", required=True, type=Path)
    gate.add_argument("--assessment", required=True, type=Path)
    gate.add_argument("--format", choices=("yaml", "json"), default="yaml")
    post = sub.add_parser("postflight")
    post.add_argument("--profile", required=True, type=Path)
    post.add_argument("--events", required=True, type=Path)
    post.add_argument("--format", choices=("yaml", "json"), default="yaml")

    args = parser.parse_args()
    try:
        if args.command == "intent-request":
            out = request_artifact(load_yaml(args.profile), args.resource_id, args.operation, args.change_boundary, args.declared_intent)
        elif args.command == "intent-finalize":
            out = finalize_intent(load_yaml(args.request), load_yaml(args.result))
        elif args.command == "intent-gate":
            out = intent_gate(load_yaml(args.profile), load_yaml(args.assessment))
            emit(out, args.format)
            return 0 if out["status"] == "COMPATIBLE" else 1
        else:
            out = postflight(load_yaml(args.profile), load_yaml(args.events))
            emit(out, args.format)
            return 0 if out["status"] == "PASS" else 1
        emit(out, args.format)
        return 0
    except (OSError, yaml.YAMLError, ValueError, AssuranceError) as exc:
        print(f"AGENT ASSURANCE BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
