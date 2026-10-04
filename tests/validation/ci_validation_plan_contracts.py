from __future__ import annotations

import sys

from .static_contracts import ROOT, errors, load_yaml

config_path = ROOT / "config/ci-validation-plan.yaml"
script_path = ROOT / "scripts/ci_validation_plan.py"
evidence_path = ROOT / "tests/evidence/ci_validation_plan_lifecycle.py"
for path in (config_path, script_path, evidence_path):
    if not path.is_file():
        errors.append(f"CI validation planning artifact missing: {path.relative_to(ROOT)}")

if config_path.is_file():
    config = load_yaml(config_path) or {}
    if config.get("version") != 1:
        errors.append("CI validation planning config version must be 1")
    if not config.get("full_validation_paths"):
        errors.append("CI validation planning must fail closed on sensitive paths")
if script_path.is_file():
    text = script_path.read_text(encoding="utf-8")
    for token in ("git", "--name-only", "unknown_path_fail_closed", "planner_error_fail_closed", "needs_node", "needs_browser", "needs_openapi"):
        if token not in text:
            errors.append(f"CI validation planner missing contract token: {token}")
    import subprocess
    result = subprocess.run([sys.executable, str(evidence_path)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        errors.append(f"CI validation planner lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
