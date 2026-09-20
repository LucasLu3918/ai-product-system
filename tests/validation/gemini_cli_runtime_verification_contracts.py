from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .static_contracts import ROOT, errors, load_yaml

REQUIRED = (
    ROOT / "tests/evidence/gemini_cli_runtime_verification.py",
    ROOT / "tests/fixtures/gemini_cli_runtime_verification/read.responses",
    ROOT / "tests/fixtures/gemini_cli_runtime_verification/write.responses",
    ROOT / "tests/fixtures/gemini_cli_runtime_verification/replace.responses",
    ROOT / "references/evolution/ISSUE_79_GEMINI_RUNTIME_VERIFICATION_BASELINE.yaml",
    ROOT / "references/evolution/ISSUE_79_GEMINI_RUNTIME_VERIFICATION_DECISION.yaml",
    ROOT / "references/evolution/ISSUE_79_GEMINI_RUNTIME_VERIFICATION_RESULT.yaml",
    ROOT / "tests/scenarios/143-gemini-cli-real-runtime-execution-verification.md",
)
for path in REQUIRED:
    if not path.exists():
        errors.append(f"Gemini real-runtime verification required file missing: {path.relative_to(ROOT)}")


def canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


decision_path = ROOT / "references/evolution/ISSUE_79_GEMINI_RUNTIME_VERIFICATION_DECISION.yaml"
baseline_path = ROOT / "references/evolution/ISSUE_79_GEMINI_RUNTIME_VERIFICATION_BASELINE.yaml"
result_path = ROOT / "references/evolution/ISSUE_79_GEMINI_RUNTIME_VERIFICATION_RESULT.yaml"

if baseline_path.exists():
    baseline = load_yaml(baseline_path) or {}
    if canonical_digest(baseline) != "sha256:62bfff09aeeab8decc352975b47e5b71d7149b834265deab7654006edb1ed47b":
        errors.append("Gemini runtime verification baseline digest changed")

if decision_path.exists():
    decision_doc = load_yaml(decision_path) or {}
    decision = decision_doc.get("decision") or {}
    if canonical_digest(decision) != decision_doc.get("decision_fingerprint"):
        errors.append("Gemini runtime verification Decision fingerprint mismatch")
    if decision.get("baseline_repository_revision") != "dac529ed2c385081547c3c3de4820f7a80b97101":
        errors.append("Gemini runtime verification Decision baseline mismatch")
    if decision.get("decision") != "TRIAL" or decision.get("human_override") is not True:
        errors.append("Gemini runtime verification requires explicit Human TRIAL override")

if result_path.exists():
    report = load_yaml(result_path) or {}
    core = dict(report)
    fingerprint = core.pop("verification_fingerprint", None)
    if canonical_digest(core) != fingerprint:
        errors.append("Gemini runtime verification result fingerprint mismatch")
    required_true = (
        "binary_execution_verified",
        "extension_loading_verified",
        "real_tool_execution_verified",
        "after_tool_hook_execution_verified",
        "live_runtime_execution_verified",
        "live_capture_verified",
    )
    for key in required_true:
        if report.get(key) is not True:
            errors.append(f"Gemini runtime verification result must keep {key}=true")
    for key in ("provider_model_api_exercised", "provider_model_execution_verified", "network_model_call_verified"):
        if report.get(key) is not False:
            errors.append(f"Gemini runtime verification must keep {key}=false")
    if report.get("gemini_cli_version") != "0.60.0":
        errors.append("Gemini runtime verification result must pin v0.60.0")
    if report.get("verified_capture_events") != 3 or report.get("unexpected_event_loss") != 0:
        errors.append("Gemini runtime verification capture evidence changed")
    if report.get("secret_private_raw_leakage") != 0 or report.get("raw_payload_persisted") is not False:
        errors.append("Gemini runtime verification leakage boundary changed")
    authority = report.get("authority") or {}
    if any(value is not False for value in authority.values()):
        errors.append("Gemini runtime verification result must grant no protected authority")

workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
for token in (
    "gemini-runtime-verification:",
    "@google/gemini-cli@0.60.0",
    "gemini_cli_runtime_verification.py",
    "needs: [janitor, gemini-runtime-verification]",
):
    if token not in workflow:
        errors.append(f"validate workflow missing real Gemini runtime gate token: {token}")

for fixture in ("read.responses", "write.responses", "replace.responses"):
    path = ROOT / "tests/fixtures/gemini_cli_runtime_verification" / fixture
    if path.exists():
        try:
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except json.JSONDecodeError as exc:
            errors.append(f"{fixture}: invalid fake-response JSONL: {exc}")
            continue
        if len(rows) != 2 or any(row.get("method") != "generateContentStream" for row in rows):
            errors.append(f"{fixture}: expected exactly two generateContentStream fake responses")
