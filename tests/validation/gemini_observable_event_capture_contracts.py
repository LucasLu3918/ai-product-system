from __future__ import annotations

import json
import subprocess
import sys

from .static_contracts import ROOT, errors, load_yaml

REQUIRED = (
    ROOT / "config/gemini-observable-event-capture.yaml",
    ROOT / "harness/adapters/gemini-cli/hooks/aips-observable-event-capture.sh",
    ROOT / "scripts/gemini_observable_event_capture.py",
    ROOT / "tests/evidence/gemini_observable_event_capture_lifecycle.py",
    ROOT / "tests/fixtures/gemini_observable_event_capture/after-tool-events.yaml",
    ROOT / "tests/fixtures/gemini_observable_event_capture/profile.yaml",
    ROOT / "references/evolution/ISSUE_79_GEMINI_LIVE_CAPTURE_TRIAL_BASELINE.yaml",
    ROOT / "references/evolution/ISSUE_79_GEMINI_LIVE_CAPTURE_TRIAL_DECISION.yaml",
    ROOT / "references/evolution/ISSUE_79_GEMINI_LIVE_CAPTURE_TRIAL_RESULT.yaml",
)
for path in REQUIRED:
    if not path.exists():
        errors.append(f"Gemini observable-event capture required file missing: {path.relative_to(ROOT)}")

hooks_path = ROOT / "harness/adapters/gemini-cli/hooks/hooks.json"
if hooks_path.exists():
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
    after = (hooks.get("hooks") or {}).get("AfterTool") or []
    if len(after) != 1 or after[0].get("matcher") != "read_file|write_file|replace":
        errors.append("Gemini adapter must wire exactly the bounded v1 AfterTool matcher")
    commands = [item for group in after for item in (group.get("hooks") or [])]
    if not any(item.get("name") == "aips-observable-event-capture" for item in commands):
        errors.append("Gemini adapter missing aips-observable-event-capture AfterTool hook")

config_path = ROOT / "config/gemini-observable-event-capture.yaml"
if config_path.exists():
    config = load_yaml(config_path) or {}
    if config.get("enabled_by_default") is not False:
        errors.append("Gemini observable-event capture must remain disabled by default")
    verification = config.get("verification") or {}
    if verification.get("live_runtime_execution_verified") is not False:
        errors.append("Gemini Trial must not claim live runtime execution")
    if verification.get("live_capture_verified") is not False:
        errors.append("Gemini Trial must not claim live capture verified")
    enforcement = config.get("enforcement") or {}
    if enforcement.get("critical_path") is not False:
        errors.append("Gemini capture critical_path must mean no authorization/result enforcement")
    if enforcement.get("critical_path_semantics") != "authorization_or_result_enforcement_only":
        errors.append("Gemini capture must define critical_path semantics explicitly")
    if enforcement.get("synchronous_hook") is not True or enforcement.get("latency_path") != "synchronous":
        errors.append("Gemini AfterTool capture must truthfully declare synchronous hook latency")
    if enforcement.get("result_flow_control_authorized") is not False:
        errors.append("Gemini capture must not authorize result-flow control")
    if any((config.get("authority") or {}).values()):
        errors.append("Gemini capture config must grant no protected authority")

script = ROOT / "scripts/gemini_observable_event_capture.py"
if script.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(script)], cwd=ROOT, capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Gemini observable-event capture syntax failed: {compiled.stderr.strip()}")

lifecycle = ROOT / "tests/evidence/gemini_observable_event_capture_lifecycle.py"
if lifecycle.exists():
    proc = subprocess.run([sys.executable, str(lifecycle)], cwd=ROOT, capture_output=True, text=True, timeout=45)
    if proc.returncode != 0:
        errors.append(f"Gemini observable-event capture lifecycle failed: {proc.stdout.strip()} {proc.stderr.strip()}")

result_path = ROOT / "references/evolution/ISSUE_79_GEMINI_LIVE_CAPTURE_TRIAL_RESULT.yaml"
if result_path.exists():
    report = load_yaml(result_path) or {}
    if report.get("status") != "PASS":
        errors.append("Gemini live-capture implementation Trial result must be PASS")
    if report.get("captured_supported_cases") != 6 or report.get("unexpected_event_loss") != 0:
        errors.append("Gemini live-capture Trial capture/loss evidence changed")
    if report.get("secret_private_raw_leakage") != 0 or report.get("raw_payload_persisted") is not False:
        errors.append("Gemini live-capture Trial must preserve zero raw/secret/private leakage")
    runtime = report.get("runtime_verification") or {}
    if runtime.get("live_runtime_execution_verified") is not False or runtime.get("live_capture_verified") is not False:
        errors.append("Gemini Trial result must not overclaim real runtime verification")
    enforcement = report.get("enforcement") or {}
    if enforcement.get("critical_path_semantics") != "authorization_or_result_enforcement_only":
        errors.append("Gemini Trial result must define critical_path semantics")
    if enforcement.get("synchronous_hook") is not True or enforcement.get("latency_path") != "synchronous":
        errors.append("Gemini Trial result must declare synchronous hook execution")
    if enforcement.get("result_flow_control_authorized") is not False:
        errors.append("Gemini Trial result must keep result-flow authority false")
    authority = report.get("authority") or {}
    if authority.get("human_adoption_decision_required") is not True:
        errors.append("Gemini Trial must still require Human review")
    for key in (
        "live_runtime_capture_authorized",
        "runtime_enforcement_authorized",
        "automatic_remediation_authorized",
        "human_approval_granted",
        "merge_authorized",
        "release_authorized",
        "publication_authorized",
    ):
        if authority.get(key) is not False:
            errors.append(f"Gemini Trial must keep authority.{key}=false")
