from __future__ import annotations

from .static_contracts import ROOT, errors, load_yaml

script = ROOT / "scripts/validation_observation.py"
lifecycle = ROOT / "tests/evidence/validation_observation_lifecycle.py"
workflow = ROOT / ".github/workflows/validation-observation-collector.yml"
validate_workflow = ROOT / ".github/workflows/validate.yml"
graduation_config = load_yaml(ROOT / "config/validation-graduation.yaml")

for path in (script, lifecycle, workflow, validate_workflow):
    if not path.is_file():
        errors.append(f"Missing validation observation artifact: {path.relative_to(ROOT)}")

if graduation_config.get("mode") != "full_run_shadow":
    errors.append("Validation observation collection must preserve full-run shadow mode")
execution = graduation_config.get("execution") or {}
if execution.get("selective_execution_enabled") is not False or execution.get("automatic_activation_authorized") is not False:
    errors.append("Validation observation collection must not authorize selective execution")

if workflow.is_file():
    import yaml
    doc = yaml.safe_load(workflow.read_text(encoding="utf-8")) or {}
    permissions = doc.get("permissions") or {}
    if permissions.get("actions") != "read" or permissions.get("contents") != "read":
        errors.append("Validation observation collector must use read-only GitHub permissions")
    if any(value in {"write", "write-all"} for value in permissions.values()):
        errors.append("Validation observation collector must not receive write permissions")

if validate_workflow.is_file():
    text = validate_workflow.read_text(encoding="utf-8")
    if "Capture combined validation observation" not in text or "retention-days: 90" not in text:
        errors.append("Validate workflow must retain combined observations for at least 90 days")

if lifecycle.is_file():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, str(lifecycle)], capture_output=True, text=True, check=False)
    if result.returncode:
        errors.append(f"Validation observation lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
