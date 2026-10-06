"""Validate the dependency impact policy and its executable contract."""
from __future__ import annotations

import subprocess
import sys

import yaml

from .static_contracts import ROOT, errors

policy_path = ROOT / "config/dependency-policy.yaml"
script_path = ROOT / "scripts/dependency_impact.py"
lifecycle_path = ROOT / "tests/evidence/dependency_impact_lifecycle.py"
for path in (policy_path, script_path, lifecycle_path):
    if not path.is_file():
        errors.append(f"Missing dependency impact artifact: {path.relative_to(ROOT)}")

if policy_path.is_file():
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    expected = {"DEV_TOOL", "CI_ACTION", "CORE_RUNTIME", "OPTIONAL_RUNTIME", "SEMANTIC_RUNTIME", "SECURITY_SENSITIVE", "UNCLASSIFIED"}
    if set(policy.get("classes", {})) != expected:
        errors.append("Dependency policy must explicitly define all seven risk classes")
    if policy.get("automatic_merge_authorized") is not False or policy.get("automatic_policy_changes_authorized") is not False:
        errors.append("Dependency policy must keep automatic merge and policy changes disabled")
    rules = {(row.get("ecosystem"), row.get("name")): row.get("class") for row in policy.get("rules", [])}
    if rules.get(("pip", "ruff")) != "DEV_TOOL":
        errors.append("Ruff must classify as DEV_TOOL")
    if rules.get(("pip", "sentence-transformers")) != "SEMANTIC_RUNTIME":
        errors.append("sentence-transformers must classify as SEMANTIC_RUNTIME")

if script_path.is_file() and lifecycle_path.is_file():
    result = subprocess.run([sys.executable, str(lifecycle_path)], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        errors.append(f"Dependency impact lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
