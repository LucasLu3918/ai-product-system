#!/usr/bin/env python3
"""Validate structured reviewer independence and exact-candidate evidence."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable

import yaml

from review_packet import ALLOWED_SOURCE_CLASSES, FINGERPRINT_RE, SHA256_RE


PROHIBITED_KEYS = {
    "chain_of_thought",
    "private_reasoning",
    "scratchpad",
    "implementation_transcript",
    "raw_model_trace",
}
MODES = {"SELF_CHECK", "INDEPENDENT_REVIEW"}
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")


class ReviewEvidenceError(ValueError):
    pass


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def prohibited_key_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            name = str(key).lower()
            path = f"{prefix}.{key}" if prefix else str(key)
            if name in PROHIBITED_KEYS:
                found.append(path)
            found.extend(prohibited_key_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(prohibited_key_paths(child, f"{prefix}[{index}]"))
    return found


def _candidate_matches(value: Any, expected: dict[str, str] | None) -> bool:
    if not isinstance(value, dict):
        return False
    keys = ("base_sha", "head_sha", "changed_files_hash")
    if any(not isinstance(value.get(key), str) for key in keys):
        return False
    if not GIT_SHA_RE.fullmatch(value["base_sha"]) or not GIT_SHA_RE.fullmatch(value["head_sha"]):
        return False
    if not FINGERPRINT_RE.fullmatch(value["changed_files_hash"]):
        return False
    return expected is None or all(value.get(key) == expected.get(key) for key in keys)


def evaluate_evidence(
    report: dict[str, Any],
    expected_candidate: dict[str, str] | None = None,
    *,
    attestation_verifier: Callable[[dict[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    if not isinstance(report, dict) or report.get("version") != 1:
        raise ReviewEvidenceError("review evidence must be a version 1 mapping")
    forbidden = prohibited_key_paths(report)
    if forbidden:
        return {"status": "FAILED", "reason_codes": ["prohibited_reasoning_field"], "field_paths": forbidden[:20]}

    mode = report.get("mode")
    if mode not in MODES:
        raise ReviewEvidenceError("review evidence mode must be SELF_CHECK or INDEPENDENT_REVIEW")
    if mode == "SELF_CHECK":
        return {"status": "SELF_CHECK", "reason_codes": ["not_independent_review"]}
    review_of_task = report.get("review_of_task")
    if not isinstance(review_of_task, str) or not review_of_task.strip():
        return {"status": "FAILED", "reason_codes": ["review_target_missing"]}

    candidate = report.get("candidate")
    if not _candidate_matches(candidate, expected_candidate):
        return {"status": "STALE", "reason_codes": ["candidate_mismatch"]}

    packet = report.get("packet")
    context = report.get("context_policy")
    permissions = report.get("permissions")
    if not isinstance(packet, dict) or not isinstance(context, dict) or not isinstance(permissions, dict):
        return {"status": "UNVERIFIED", "reason_codes": ["required_evidence_missing"]}

    packet_fingerprint = packet.get("fingerprint")
    if not isinstance(packet_fingerprint, str) or not SHA256_RE.fullmatch(packet_fingerprint):
        return {"status": "FAILED", "reason_codes": ["invalid_packet_fingerprint"]}
    source_classes = packet.get("source_classes")
    if not isinstance(source_classes, list) or not source_classes or any(
        not isinstance(source_class, str) or source_class not in ALLOWED_SOURCE_CLASSES for source_class in source_classes
    ):
        return {"status": "FAILED", "reason_codes": ["non_allowlisted_context_class"]}
    if sorted(set(source_classes)) != sorted(set(context.get("allowed_classes") or [])):
        return {"status": "FAILED", "reason_codes": ["context_class_mismatch"]}
    if context.get("inheritance") != "none":
        return {"status": "FAILED", "reason_codes": ["implementer_context_inherited"]}
    denied_classes = context.get("denied_classes")
    required_denied = {"implementation_transcript", "private_reasoning", "scratchpad", "raw_model_trace"}
    if (
        not isinstance(denied_classes, list)
        or any(not isinstance(source_class, str) for source_class in denied_classes)
        or not required_denied.issubset(set(denied_classes))
    ):
        return {"status": "FAILED", "reason_codes": ["prohibited_context_policy_incomplete"]}
    if context.get("packet_fingerprint") != packet_fingerprint:
        return {"status": "FAILED", "reason_codes": ["context_packet_mismatch"]}

    implementation_id = report.get("implementer_execution_id")
    reviewer_id = report.get("reviewer_execution_id")
    if implementation_id is not None and not isinstance(implementation_id, str):
        return {"status": "FAILED", "reason_codes": ["invalid_execution_identity"]}
    if reviewer_id is not None and not isinstance(reviewer_id, str):
        return {"status": "FAILED", "reason_codes": ["invalid_execution_identity"]}
    if implementation_id and reviewer_id and implementation_id == reviewer_id:
        return {"status": "FAILED", "reason_codes": ["same_execution_identity"]}
    if not implementation_id or not reviewer_id:
        return {"status": "UNVERIFIED", "reason_codes": ["execution_identity_unavailable"]}
    if permissions.get("read_only") is not True or permissions.get("write_set") != []:
        return {"status": "FAILED", "reason_codes": ["reviewer_write_authority_present"]}

    attestation = report.get("runtime_attestation")
    if not isinstance(attestation, dict):
        return {"status": "UNVERIFIED", "reason_codes": ["runtime_attestation_unavailable"]}
    checks = ("execution_identity", "context_isolation", "read_only_authority")
    values = [attestation.get(key) for key in checks]
    if any(value == "FAILED" for value in values):
        return {"status": "FAILED", "reason_codes": ["runtime_isolation_failed"]}
    if not all(value == "VERIFIED" for value in values):
        return {"status": "UNVERIFIED", "reason_codes": ["runtime_isolation_unverified"]}
    if not isinstance(attestation.get("runtime"), str) or not attestation["runtime"].strip():
        return {"status": "UNVERIFIED", "reason_codes": ["runtime_identity_missing"]}
    if not isinstance(attestation.get("receipt_ref"), str) or not attestation["receipt_ref"].strip():
        return {"status": "UNVERIFIED", "reason_codes": ["runtime_receipt_missing"]}
    receipt_hash = attestation.get("receipt_sha256")
    if not isinstance(receipt_hash, str) or not SHA256_RE.fullmatch(receipt_hash):
        return {"status": "UNVERIFIED", "reason_codes": ["runtime_receipt_fingerprint_missing"]}
    issuer_key_id = attestation.get("issuer_key_id")
    signature = attestation.get("signature_b64")
    if not isinstance(issuer_key_id, str) or not issuer_key_id.strip():
        return {"status": "UNVERIFIED", "reason_codes": ["runtime_attestation_issuer_missing"]}
    if attestation.get("signature_algorithm") != "ed25519" or not isinstance(signature, str):
        return {"status": "UNVERIFIED", "reason_codes": ["runtime_attestation_signature_missing"]}
    try:
        base64.b64decode(signature, validate=True)
    except (ValueError, binascii.Error):
        return {"status": "FAILED", "reason_codes": ["runtime_attestation_signature_invalid_encoding"]}
    if attestation.get("packet_fingerprint") != packet_fingerprint:
        return {"status": "FAILED", "reason_codes": ["runtime_attestation_packet_mismatch"]}
    if attestation_verifier is None:
        return {"status": "UNVERIFIED", "reason_codes": ["trusted_runtime_attestation_verifier_unavailable"]}
    try:
        attestation_is_trusted = attestation_verifier(attestation)
    except Exception:
        return {"status": "UNVERIFIED", "reason_codes": ["runtime_attestation_verification_error"]}
    if not attestation_is_trusted:
        return {"status": "UNVERIFIED", "reason_codes": ["runtime_attestation_untrusted"]}

    unresolved = report.get("unresolved_blocking_findings", 0)
    if isinstance(unresolved, bool) or not isinstance(unresolved, int) or unresolved < 0:
        raise ReviewEvidenceError("unresolved_blocking_findings must be a non-negative integer")
    if unresolved:
        return {"status": "FAILED", "reason_codes": ["unresolved_blocking_findings"]}
    return {"status": "VERIFIED", "reason_codes": []}


def validate_report(
    root: Path,
    report_path: Path,
    expected_candidate: dict[str, str],
    *,
    allow_external: bool = False,
) -> dict[str, Any]:
    repo = root.resolve()
    resolved = report_path if report_path.is_absolute() else repo / report_path
    resolved = resolved.resolve()
    inside_repo = resolved.is_relative_to(repo)
    if (not inside_repo and not allow_external) or not resolved.is_file():
        return {"status": "UNVERIFIED", "reason_codes": ["review_evidence_file_missing_or_outside_repo"]}
    try:
        report = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError):
        return {"status": "FAILED", "reason_codes": ["review_evidence_unreadable"]}
    try:
        result = evaluate_evidence(report, expected_candidate)
    except ReviewEvidenceError:
        result = {"status": "FAILED", "reason_codes": ["invalid_review_evidence_schema"]}
    result["evidence_path"] = resolved.relative_to(repo).as_posix() if inside_repo else "external_artifact"
    result["evidence_sha256"] = "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--changed-files-hash", required=True)
    args = parser.parse_args()
    candidate = {
        "base_sha": args.base,
        "head_sha": args.head,
        "changed_files_hash": args.changed_files_hash,
    }
    try:
        result = validate_report(args.root, args.evidence, candidate)
    except ReviewEvidenceError as exc:
        print(f"REVIEW EVIDENCE BLOCKED: {exc}")
        return 2
    print(yaml.safe_dump(result, sort_keys=False))
    return 0 if result["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
