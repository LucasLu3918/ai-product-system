#!/usr/bin/env python3
"""Deterministic offline benchmark for out-of-band Agent anomaly evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml

from resource_authorization import MUTATING, OPERATIONS, canonical_hash as authorization_hash
from resource_authorization import decision as authorization_decision
from resource_authorization import validate_profile

OUTCOMES = {"SUCCESS", "DENIED", "FAILED"}
PROTECTED_OPERATIONS = {
    "merge",
    "release",
    "publication",
    "administration",
    "destructive_delete",
    "human_approval",
}
FORBIDDEN_KEYS = {
    "analysis",
    "chain_of_thought",
    "chain-of-thought",
    "cot",
    "private_reasoning",
    "reasoning_trace",
    "scratchpad",
    "thoughts",
    "password",
    "api_key",
    "token",
    "secret_value",
}
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:password|api[_-]?key|secret|token)\s*[:=]\s*[^\s,;]{8,}"),
)

PRIVATE_REASONING_KEYS = {
    "analysis",
    "chain_of_thought",
    "chain-of-thought",
    "cot",
    "private_reasoning",
    "reasoning_trace",
    "scratchpad",
    "thoughts",
}


class EvaluationError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise EvaluationError(f"{path}: expected mapping")
    return value


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def forbidden_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).strip().lower() in FORBIDDEN_KEYS:
                found.append(path)
            found.extend(forbidden_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(forbidden_paths(child, f"{prefix}[{index}]"))
    return found


def private_reasoning_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).strip().lower() in PRIVATE_REASONING_KEYS:
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
    elif isinstance(value, str) and any(pattern.search(value) for pattern in SECRET_PATTERNS):
        findings.append(prefix or "<root>")
    return findings


def authority() -> dict[str, bool]:
    return {
        "human_approval_granted": False,
        "runtime_enforcement_authorized": False,
        "automatic_remediation_authorized": False,
        "merge_authorized": False,
        "release_authorized": False,
        "publication_authorized": False,
        "protected_operation_authorized": False,
    }


def enforcement() -> dict[str, Any]:
    return {
        "mode": "POST_EXECUTION_EVIDENCE",
        "runtime_enforced": False,
        "critical_path": False,
        "automatic_remediation": False,
        "provider_required": False,
    }


def validate_corpus(corpus: dict[str, Any], profile: dict[str, Any]) -> None:
    validate_profile(profile)
    if corpus.get("version") != 1:
        raise EvaluationError("corpus.version must be 1")
    if not str(corpus.get("evaluation_id") or "").strip():
        raise EvaluationError("evaluation_id is required")
    if forbidden_paths(corpus):
        raise EvaluationError("private reasoning or secret-value fields are prohibited")
    if secret_findings(corpus):
        raise EvaluationError("secret-like values are prohibited")

    thresholds = corpus.get("thresholds")
    if not isinstance(thresholds, dict):
        raise EvaluationError("thresholds must be a mapping")
    for key in ("min_precision", "min_recall", "max_false_positive_rate", "max_false_negative_rate"):
        value = thresholds.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
            raise EvaluationError(f"thresholds.{key} must be between 0 and 1")

    cases = corpus.get("cases")
    if not isinstance(cases, list) or not cases:
        raise EvaluationError("cases must be a non-empty list")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise EvaluationError("each case must be a mapping")
        case_id = str(case.get("id") or "").strip()
        if not case_id or case_id in seen:
            raise EvaluationError("case ids must be non-empty and unique")
        seen.add(case_id)
        if not isinstance(case.get("expected_anomaly"), bool):
            raise EvaluationError(f"{case_id}: expected_anomaly must be boolean")
        expected_types = case.get("expected_types") or []
        if not isinstance(expected_types, list) or not all(isinstance(x, str) and x.strip() for x in expected_types):
            raise EvaluationError(f"{case_id}: expected_types must be strings")
        event = case.get("event")
        if not isinstance(event, dict):
            raise EvaluationError(f"{case_id}: event must be a mapping")
        for key in ("subject", "resource_id", "operation", "observed_outcome"):
            if not str(event.get(key) or "").strip():
                raise EvaluationError(f"{case_id}: event.{key} is required")
        if event["observed_outcome"] not in OUTCOMES:
            raise EvaluationError(f"{case_id}: unsupported observed_outcome")
        if not isinstance(event.get("network_used", False), bool):
            raise EvaluationError(f"{case_id}: network_used must be boolean")


def _grant(profile: dict[str, Any], resource_id: str) -> dict[str, Any] | None:
    return next((item for item in profile.get("grants") or [] if item.get("id") == resource_id), None)


def detect(event: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, str]]:
    anomalies: list[dict[str, str]] = []
    subject = str(event["subject"])
    resource_id = str(event["resource_id"])
    operation = str(event["operation"])
    outcome = str(event["observed_outcome"])
    change_boundary = event.get("change_boundary")

    if subject != str((profile.get("subject") or {}).get("id")):
        anomalies.append({"type": "subject_mismatch", "severity": "HIGH"})

    if operation in PROTECTED_OPERATIONS:
        anomalies.append({"type": "protected_operation_observed", "severity": "HIGH"})
        return anomalies

    if operation not in OPERATIONS:
        anomalies.append({"type": "unsupported_operation_observed", "severity": "HIGH"})
        return anomalies

    auth = authorization_decision(profile, resource_id, operation, change_boundary)
    grant = _grant(profile, resource_id)
    constraints = (grant or {}).get("constraints") or {}

    if auth["status"] == "DENY" and outcome == "SUCCESS":
        anomalies.append({"type": "unauthorized_success", "severity": "HIGH"})

    if (
        grant is not None
        and operation in MUTATING
        and constraints.get("change_boundary_required") is True
        and not change_boundary
        and outcome == "SUCCESS"
    ):
        anomalies.append({"type": "missing_required_change_boundary", "severity": "HIGH"})

    if grant is not None and event.get("network_used", False) and constraints.get("network_allowed") is False:
        anomalies.append({"type": "network_policy_violation", "severity": "HIGH"})

    return anomalies


def _ratio(numerator: int, denominator: int, *, empty: float) -> float:
    return empty if denominator == 0 else numerator / denominator


def evaluate(corpus: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    validate_corpus(corpus, profile)
    case_results: list[dict[str, Any]] = []
    tp = fp = tn = fn = 0

    for case in corpus["cases"]:
        anomalies = detect(case["event"], profile)
        detected = bool(anomalies)
        expected = bool(case["expected_anomaly"])
        if expected and detected:
            tp += 1
        elif not expected and detected:
            fp += 1
        elif not expected and not detected:
            tn += 1
        else:
            fn += 1
        detected_types = sorted({item["type"] for item in anomalies})
        expected_types = sorted(set(case.get("expected_types") or []))
        type_match = set(expected_types).issubset(detected_types)
        case_results.append(
            {
                "id": case["id"],
                "expected_anomaly": expected,
                "detected_anomaly": detected,
                "expected_types": expected_types,
                "detected_types": detected_types,
                "classification_correct": expected == detected and type_match,
            }
        )

    precision = _ratio(tp, tp + fp, empty=1.0)
    recall = _ratio(tp, tp + fn, empty=1.0)
    fpr = _ratio(fp, fp + tn, empty=0.0)
    fnr = _ratio(fn, fn + tp, empty=0.0)
    thresholds = corpus["thresholds"]
    metrics = {
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "false_positive_rate": round(fpr, 6),
        "false_negative_rate": round(fnr, 6),
    }
    threshold_pass = (
        precision >= float(thresholds["min_precision"])
        and recall >= float(thresholds["min_recall"])
        and fpr <= float(thresholds["max_false_positive_rate"])
        and fnr <= float(thresholds["max_false_negative_rate"])
        and all(item["classification_correct"] for item in case_results)
    )

    return {
        "version": 1,
        "status": "PASS" if threshold_pass else "FAIL",
        "evaluation_id": corpus["evaluation_id"],
        "profile_fingerprint": "sha256:" + authorization_hash(profile),
        "corpus_fingerprint": digest(corpus),
        "case_count": len(case_results),
        "metrics": metrics,
        "thresholds": thresholds,
        "cases": case_results,
        "recommendation": "HUMAN_REVIEW_TRIAL_EVIDENCE" if threshold_pass else "HOLD",
        "enforcement": enforcement(),
        "authority": authority(),
    }


def emit(value: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--profile", required=True, type=Path)
    validate.add_argument("--corpus", required=True, type=Path)

    evaluate_cmd = sub.add_parser("evaluate")
    evaluate_cmd.add_argument("--profile", required=True, type=Path)
    evaluate_cmd.add_argument("--corpus", required=True, type=Path)
    evaluate_cmd.add_argument("--output", type=Path)

    args = parser.parse_args()
    try:
        profile = load_yaml(args.profile)
        corpus = load_yaml(args.corpus)
        validate_corpus(corpus, profile)
        if args.command == "validate":
            result = {
                "version": 1,
                "status": "PASS",
                "evaluation_id": corpus["evaluation_id"],
                "profile_fingerprint": "sha256:" + authorization_hash(profile),
                "corpus_fingerprint": digest(corpus),
                "case_count": len(corpus["cases"]),
                "enforcement": enforcement(),
                "authority": authority(),
            }
            print(emit(result, args.format), end="")
            return 0

        result = evaluate(corpus, profile)
        rendered = emit(result, args.format)
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0 if result["status"] == "PASS" else 1
    except (OSError, yaml.YAMLError, ValueError, EvaluationError) as exc:
        print(f"AGENT ANOMALY EVALUATION BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
