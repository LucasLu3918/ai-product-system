#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts" / "agent_assurance.py"
CLI = ROOT / "bin" / "aips"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(HELPER), *args, "--format", "json"], capture_output=True, text=True)


def write(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    profile_path = root / "profile.yaml"
    profile = {
        "version": 1,
        "default_effect": "DENY",
        "subject": {"id": "implementation-agent", "role": "backend-engineer"},
        "grants": [{
            "id": "application-source",
            "kind": "repository_path",
            "selector": "src/**",
            "operations": ["read", "update"],
            "constraints": {"change_boundary_required": True, "network_allowed": False},
        }],
        "authority": {
            "human_approval_granted": False,
            "merge_authorized": False,
            "release_authorized": False,
            "protected_operation_authorized": False,
        },
    }
    write(profile_path, profile)

    request_proc = run(
        "intent-request", "--profile", str(profile_path),
        "--resource-id", "application-source", "--operation", "update",
        "--change-boundary", "orders",
        "--declared-intent", "Update refund validation inside the approved orders boundary",
    )
    assert request_proc.returncode == 0, request_proc.stderr
    request = json.loads(request_proc.stdout)
    assert request["request"]["authorization_status"] == "ALLOW"
    assert request["authority"]["tool_call_authorized"] is False
    request_path = root / "request.yaml"
    write(request_path, request)

    secret_request = run(
        "intent-request", "--profile", str(profile_path),
        "--resource-id", "application-source", "--operation", "read",
        "--declared-intent", "api_key=super-secret-value",
    )
    assert secret_request.returncode == 2

    aligned_result = {
        "version": 1,
        "request_fingerprint": request["request_fingerprint"],
        "assessment": {
            "state": "ALIGNED",
            "confidence": 0.93,
            "summary": "Declared intent matches the requested bounded source update.",
            "evidence": ["request:declared_intent", "request:resource_id"],
            "provider": "test-provider",
            "model": "test-model",
            "assessed_at": "2026-09-19T00:00:00Z",
        },
        "authority": {"tool_call_authorized": False},
    }
    aligned_path = root / "aligned.yaml"
    write(aligned_path, aligned_result)
    finalize = run("intent-finalize", "--request", str(request_path), "--result", str(aligned_path))
    assert finalize.returncode == 0, finalize.stderr
    artifact = json.loads(finalize.stdout)
    assert artifact["enforcement"]["can_only_narrow_authorization"] is True
    assessment_path = root / "assessment.yaml"
    write(assessment_path, artifact)

    gate = run("intent-gate", "--profile", str(profile_path), "--assessment", str(assessment_path))
    assert gate.returncode == 0, gate.stderr
    gate_doc = json.loads(gate.stdout)
    assert gate_doc["status"] == "COMPATIBLE"
    assert gate_doc["authority"]["tool_call_authorized"] is False

    misaligned = dict(aligned_result)
    misaligned["assessment"] = dict(aligned_result["assessment"])
    misaligned["assessment"]["state"] = "MISALIGNED"
    misaligned["assessment"]["summary"] = "Declared intent conflicts with the bounded operation."
    misaligned_path = root / "misaligned.yaml"
    write(misaligned_path, misaligned)
    finalize_bad = run("intent-finalize", "--request", str(request_path), "--result", str(misaligned_path))
    assert finalize_bad.returncode == 0
    blocked_path = root / "blocked.yaml"
    write(blocked_path, json.loads(finalize_bad.stdout))
    blocked = run("intent-gate", "--profile", str(profile_path), "--assessment", str(blocked_path))
    assert blocked.returncode == 1
    assert json.loads(blocked.stdout)["status"] == "BLOCKED"

    denied_request = run(
        "intent-request", "--profile", str(profile_path),
        "--resource-id", "application-source", "--operation", "update",
        "--declared-intent", "Update without a Change Boundary",
    )
    assert denied_request.returncode == 0
    denied_doc = json.loads(denied_request.stdout)
    assert denied_doc["request"]["authorization_status"] == "DENY"
    denied_request_path = root / "denied-request.yaml"
    write(denied_request_path, denied_doc)
    denied_result = dict(aligned_result)
    denied_result["request_fingerprint"] = denied_doc["request_fingerprint"]
    denied_result_path = root / "denied-result.yaml"
    write(denied_result_path, denied_result)
    denied_final = run("intent-finalize", "--request", str(denied_request_path), "--result", str(denied_result_path))
    assert denied_final.returncode == 0
    denied_assessment_path = root / "denied-assessment.yaml"
    write(denied_assessment_path, json.loads(denied_final.stdout))
    denied_gate = run("intent-gate", "--profile", str(profile_path), "--assessment", str(denied_assessment_path))
    assert denied_gate.returncode == 1
    assert json.loads(denied_gate.stdout)["reason"] == "resource_authorization_denied"

    secret_result = dict(aligned_result)
    secret_result["assessment"] = dict(aligned_result["assessment"])
    secret_result["assessment"]["summary"] = "api_key=super-secret-value"
    secret_path = root / "secret.yaml"
    write(secret_path, secret_result)
    assert run("intent-finalize", "--request", str(request_path), "--result", str(secret_path)).returncode == 2

    clean_events = {
        "version": 1,
        "subject": "implementation-agent",
        "events": [
            {"id": "event-1", "resource_id": "application-source", "operation": "update", "change_boundary": "orders", "observed_outcome": "SUCCESS", "network_used": False},
            {"id": "event-2", "resource_id": "unknown", "operation": "read", "observed_outcome": "DENIED", "network_used": False},
        ],
    }
    clean_path = root / "clean-events.yaml"
    write(clean_path, clean_events)
    audit = run("postflight", "--profile", str(profile_path), "--events", str(clean_path))
    assert audit.returncode == 0, audit.stderr
    audit_doc = json.loads(audit.stdout)
    assert audit_doc["status"] == "PASS"
    assert audit_doc["summary"]["expected_denials"] == 1
    assert audit_doc["events_fingerprint"].startswith("sha256:")
    assert audit_doc["enforcement"]["critical_path"] is False
    assert audit_doc["enforcement"]["automatic_remediation"] is False

    anomalous = {
        "version": 1,
        "subject": "implementation-agent",
        "events": [
            {"id": "event-3", "resource_id": "unknown", "operation": "read", "observed_outcome": "SUCCESS", "network_used": False},
            {"id": "event-4", "resource_id": "application-source", "operation": "read", "observed_outcome": "SUCCESS", "network_used": True},
        ],
    }
    anomalous_path = root / "anomalous-events.yaml"
    write(anomalous_path, anomalous)
    review = run("postflight", "--profile", str(profile_path), "--events", str(anomalous_path))
    assert review.returncode == 1
    review_doc = json.loads(review.stdout)
    kinds = {item["type"] for item in review_doc["anomalies"]}
    assert review_doc["status"] == "REVIEW"
    assert "unauthorized_success" in kinds
    assert "network_policy_violation" in kinds
    assert review_doc["authority"]["automatic_remediation_authorized"] is False

    cli = subprocess.run(
        ["bash", str(CLI), "assurance", "postflight", "--profile", str(profile_path), "--events", str(clean_path), "--format", "json"],
        capture_output=True, text=True,
    )
    assert cli.returncode == 0, cli.stderr
    assert json.loads(cli.stdout)["status"] == "PASS"

print("agent runtime assurance lifecycle: PASS")
