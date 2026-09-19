from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors, load_yaml

REQUIRED = (
    ROOT / "config/agent-observable-event-trial.yaml",
    ROOT / "orchestration/schemas/agent-observable-event.yaml",
    ROOT / "scripts/agent_observable_event_trial.py",
    ROOT / "tests/evidence/agent_observable_event_trial_lifecycle.py",
    ROOT / "tests/fixtures/agent_observable_event_trial/raw-events.yaml",
    ROOT / "references/evolution/ISSUE_79_AGENT_ANOMALY_TRIAL_BASELINE.yaml",
    ROOT / "references/evolution/ISSUE_79_AGENT_ANOMALY_TRIAL_DECISION.yaml",
    ROOT / "references/evolution/ISSUE_79_AGENT_OBSERVABLE_EVENT_TRIAL_RESULT.yaml",
)
for path in REQUIRED:
    if not path.exists():
        errors.append(f"Observable-event Trial required file missing: {path.relative_to(ROOT)}")

config_path = ROOT / "config/agent-observable-event-trial.yaml"
if config_path.exists():
    config = load_yaml(config_path) or {}
    if config.get("mode") != "ADAPTER_EXPORT_REPLAY":
        errors.append("Observable-event Trial must remain replay-only")
    if config.get("live_capture_verified") is not False or config.get("raw_payload_persisted") is not False:
        errors.append("Observable-event Trial must not claim live capture or raw payload persistence")
    authority = config.get("authority") or {}
    if any(value is not False for value in authority.values()):
        errors.append("Observable-event Trial config must not grant authority")

script = ROOT / "scripts/agent_observable_event_trial.py"
if script.exists():
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(script)], cwd=ROOT, text=True, capture_output=True)
    if compiled.returncode != 0:
        errors.append(f"observable-event Trial syntax failed: {compiled.stderr.strip()}")

lifecycle = ROOT / "tests/evidence/agent_observable_event_trial_lifecycle.py"
if lifecycle.exists():
    result = subprocess.run([sys.executable, str(lifecycle)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        errors.append(f"observable-event Trial lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")

result_path = ROOT / "references/evolution/ISSUE_79_AGENT_OBSERVABLE_EVENT_TRIAL_RESULT.yaml"
if result_path.exists():
    report = load_yaml(result_path) or {}
    metrics = report.get("metrics") or {}
    expected = {
        "true_positive": 6,
        "false_positive": 0,
        "true_negative": 6,
        "false_negative": 0,
        "precision": 1.0,
        "recall": 1.0,
        "false_positive_rate": 0.0,
        "false_negative_rate": 0.0,
    }
    if metrics != expected:
        errors.append("Committed observable-event Trial metrics do not match bounded fixture")
    if report.get("status") != "PASS" or report.get("recommendation") != "HUMAN_REVIEW_TRIAL_RESULT":
        errors.append("Observable-event Trial PASS must stop at Human review")
    if report.get("live_capture_verified") is not False or report.get("raw_payload_persisted") is not False:
        errors.append("Observable-event Trial report overclaims capture/persistence")
    authority = report.get("authority") or {}
    if authority.get("human_adoption_decision_required") is not True:
        errors.append("Observable-event Trial must still require Human adoption decision")
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
            errors.append(f"Observable-event Trial report must keep {key}=false")
