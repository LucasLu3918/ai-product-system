from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors, load_yaml

REQUIRED = (
    ROOT / "scripts/agent_observable_event_capture.py",
    ROOT / "scripts/manage_runtime_adapter.py",
    ROOT / "harness/adapters/REGISTRY.yaml",
    ROOT / "references/evolution/ISSUE_79_CODEX_CAPTURE_TRIAL_BASELINE.yaml",
    ROOT / "references/evolution/ISSUE_79_CODEX_CAPTURE_TRIAL_DECISION.yaml",
    ROOT / "references/evolution/ISSUE_79_CODEX_CAPTURE_TRIAL_RESULT.yaml",
    ROOT / "tests/evidence/codex_live_capture_trial_lifecycle.py",
    ROOT / "tests/scenarios/142-codex-post-tool-live-capture-trial.md",
)
for path in REQUIRED:
    if not path.exists():
        errors.append(f"Codex live-capture Trial required file missing: {path.relative_to(ROOT)}")

for rel in ("scripts/agent_observable_event_capture.py", "scripts/manage_runtime_adapter.py"):
    path = ROOT / rel
    if path.exists():
        result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Codex capture syntax failed: {rel}: {result.stderr.strip()}")

sys.path.insert(0, str(ROOT / "scripts"))
try:
    import evolution_analysis
    import evolution_decision

    baseline = load_yaml(ROOT / "references/evolution/ISSUE_79_CODEX_CAPTURE_TRIAL_BASELINE.yaml") or {}
    decision = load_yaml(ROOT / "references/evolution/ISSUE_79_CODEX_CAPTURE_TRIAL_DECISION.yaml") or {}
    trial_result = load_yaml(ROOT / "references/evolution/ISSUE_79_CODEX_CAPTURE_TRIAL_RESULT.yaml") or {}

    if evolution_analysis.canonical_digest(baseline) != (decision.get("decision") or {}).get("evidence_digest"):
        errors.append("Codex capture TRIAL Decision does not bind the current baseline evidence digest")
    for problem in evolution_decision.validate_decision(decision):
        errors.append(f"Codex capture TRIAL Decision invalid: {problem}")

    core = {key: value for key, value in trial_result.items() if key not in {"version", "trial_fingerprint", "authority"}}
    if evolution_analysis.canonical_digest(core) != trial_result.get("trial_fingerprint"):
        errors.append("Codex capture Trial fingerprint mismatch")
    if trial_result.get("status") != "PASS" or trial_result.get("recommendation") != "HUMAN_REVIEW_RUNTIME_SMOKE_TEST":
        errors.append("Codex capture Trial PASS must stop at Human runtime smoke-test review")

    hook = trial_result.get("hook") or {}
    if hook.get("event") != "PostToolUse" or hook.get("async") is not True or hook.get("timeout_seconds") != 2:
        errors.append("Codex capture Trial hook contract drifted")
    if hook.get("hook_contract_verified") is not True:
        errors.append("Codex capture Trial must verify the hook contract")
    if hook.get("live_runtime_exercised") is not False or hook.get("live_capture_verified") is not False:
        errors.append("Codex capture Trial must not overclaim real-session verification")

    capture_state = trial_result.get("capture") or {}
    for key in ("default_enabled", "critical_path", "runtime_enforced", "automatic_remediation", "raw_payload_persisted", "private_reasoning_persisted", "secret_values_persisted"):
        if capture_state.get(key) is not False:
            errors.append(f"Codex capture Trial must keep capture.{key}=false")

    authority = trial_result.get("authority") or {}
    if authority.get("human_runtime_smoke_test_required") is not True:
        errors.append("Codex capture Trial must require a Human runtime smoke test")
    for key in ("live_runtime_capture_authorized", "runtime_enforcement_authorized", "automatic_remediation_authorized", "human_approval_granted", "merge_authorized", "release_authorized", "publication_authorized"):
        if authority.get(key) is not False:
            errors.append(f"Codex capture Trial must keep authority.{key}=false")
except Exception as exc:
    errors.append(f"Codex capture Trial contract validation failed: {exc}")

registry = load_yaml(ROOT / "harness/adapters/REGISTRY.yaml") or {}
codex = ((registry.get("adapters") or {}).get("codex") or {})
capture_state = codex.get("observable_event_capture") or {}
if capture_state.get("hook_event") != "PostToolUse":
    errors.append("Codex registry must declare PostToolUse capture")
if capture_state.get("default_enabled") is not False:
    errors.append("Codex capture must remain disabled by default")
if capture_state.get("hook_contract_verified") is not True:
    errors.append("Codex registry hook contract must be verified")
if capture_state.get("hook_trust_verified") is not False or capture_state.get("live_capture_verified") is not False:
    errors.append("Codex registry must not claim trust/live capture verification")

lifecycle = ROOT / "tests/evidence/codex_live_capture_trial_lifecycle.py"
if lifecycle.exists():
    focused = subprocess.run([sys.executable, str(lifecycle)], cwd=ROOT, capture_output=True, text=True, timeout=45)
    if focused.returncode != 0:
        errors.append(f"Codex live-capture Trial lifecycle failed: {focused.stdout.strip()} {focused.stderr.strip()}")
