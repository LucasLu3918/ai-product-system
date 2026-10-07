from __future__ import annotations

import subprocess
import sys

import yaml

from .static_contracts import ROOT, errors

config_path = ROOT / "config/eval-freshness.yaml"
script_path = ROOT / "scripts/agent_eval_freshness.py"
evidence_path = ROOT / "tests/evidence/agent_eval_freshness_lifecycle.py"
scenario_path = ROOT / "tests/scenarios/229-agent-eval-freshness.md"
for path in (config_path, script_path, evidence_path, scenario_path):
    if not path.is_file():
        errors.append(f"Missing Agent Eval freshness artifact: {path.relative_to(ROOT)}")

if config_path.is_file():
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if config.get("version") != 1:
        errors.append("Eval freshness config version must remain 1")
    if config.get("manual_scenarios") != ["192", "193", "224"]:
        errors.append("Scenarios 192, 193 and 224 must remain manual")
    if any((config.get("authority") or {}).values()):
        errors.append("Eval freshness must not execute cases or mutate cases/results")
    if evidence_path.is_file():
        result = subprocess.run([sys.executable, str(evidence_path)], cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode:
            errors.append(f"Agent Eval freshness lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
