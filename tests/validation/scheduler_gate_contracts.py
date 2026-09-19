from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors, load_yaml

REQUIRED = (
    "orchestration/DETERMINISTIC_SCHEDULER.md",
    "orchestration/INTEGRATION_GATE.md",
    "orchestration/schemas/task-graph.yaml",
    "templates/automation/TASK_GRAPH.yaml",
    "templates/automation/VALIDATION_PROFILE.yaml",
    "templates/review/INTEGRATION_GATE_REPORT.yaml",
    "config/integration-gate.yaml",
    "scripts/deterministic_scheduler.py",
    "scripts/integration_gate.py",
    "requirements-validation.txt",
    "tests/evidence/deterministic_scheduler_lifecycle.py",
    "tests/evidence/integration_gate_lifecycle.py",
    "tests/scenarios/135-deterministic-multi-agent-scheduler.md",
    "tests/scenarios/136-exact-candidate-integration-gate.md",
)
for rel in REQUIRED:
    if not (ROOT / rel).exists():
        errors.append(f"Scheduler/Integration Gate required file missing: {rel}")

for rel, keys in {
    "orchestration/schemas/task-graph.yaml": ("version", "plan_id", "base_revision", "max_parallel", "tasks"),
    "templates/automation/TASK_GRAPH.yaml": ("version", "plan_id", "base_revision", "max_parallel", "tasks"),
    "templates/automation/VALIDATION_PROFILE.yaml": ("version", "profile_id", "matrix_required", "checks"),
    "templates/review/INTEGRATION_GATE_REPORT.yaml": ("version", "candidate", "candidate_fingerprint", "checks", "status", "authority"),
    "config/integration-gate.yaml": ("version", "profile_id", "matrix_required", "checks"),
}.items():
    doc = load_yaml(ROOT / rel) or {}
    for key in keys:
        if key not in doc:
            errors.append(f"{rel} missing top-level key: {key}")

profile = load_yaml(ROOT / "config/integration-gate.yaml") or {}
categories = {str(item.get("category")) for item in (profile.get("checks") or []) if isinstance(item, dict)}
for category in ("lint", "type", "test"):
    if category not in categories:
        errors.append(f"integration gate profile missing required category: {category}")
if not any(isinstance(item, dict) and item.get("id") == "repository-validation" for item in (profile.get("checks") or [])):
    errors.append("integration gate profile must include repository-validation")

cli = (ROOT / "bin/aips").read_text(encoding="utf-8")
for phrase in ("aips scheduler --graph", "aips integration-gate --profile", "integration-gate|janitor)", "scripts/deterministic_scheduler.py", "scripts/integration_gate.py"):
    if phrase not in cli:
        errors.append(f"bin/aips missing Scheduler/Integration Gate CLI contract: {phrase}")

workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
for phrase in (
    "janitor:",
    "repository:\n    needs: janitor",
    "needs.janitor.result",
    "requirements-validation.txt",
    "scripts/integration_gate.py",
    "github.event.pull_request.head.sha",
    "AIPS_GATE_BASE_TIP",
    "Refresh pull request base tip",
    "--base-tip",
):
    if phrase not in workflow:
        errors.append(f"validate workflow missing Integration Gate contract: {phrase}")

scheduler_doc = (ROOT / "orchestration/DETERMINISTIC_SCHEDULER.md").read_text(encoding="utf-8")
for phrase in ("Structured Task Graph", "Change Boundary", "same Task Graph + state", "SCHEDULER BLOCKED", "read_only"):
    if phrase not in scheduler_doc:
        errors.append(f"DETERMINISTIC_SCHEDULER.md missing: {phrase}")

gate_doc = (ROOT / "orchestration/INTEGRATION_GATE.md").read_text(encoding="utf-8")
for phrase in ("Exact-candidate binding", "Validation Profile", "Core Change Test Matrix reuse", "repository required aggregate", "base freshness"):
    if phrase not in gate_doc:
        errors.append(f"INTEGRATION_GATE.md missing: {phrase}")

for evidence in (
    ROOT / "tests/evidence/deterministic_scheduler_lifecycle.py",
    ROOT / "tests/evidence/integration_gate_lifecycle.py",
):
    if evidence.exists():
        proc = subprocess.run([sys.executable, str(evidence)], cwd=ROOT, text=True, capture_output=True)
        if proc.returncode != 0:
            errors.append(f"Scheduler/Integration Gate lifecycle failed: {evidence.relative_to(ROOT)}: {proc.stdout.strip()} {proc.stderr.strip()}")
