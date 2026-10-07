from __future__ import annotations

import subprocess
import sys

import yaml

from .static_contracts import ROOT, errors

config_path = ROOT / "config/quality-ratchet.yaml"
script_path = ROOT / "scripts/quality_ratchet.py"
property_path = ROOT / "tests/evidence/release_channel_properties.py"
for path in (config_path, script_path, property_path):
    if not path.is_file():
        errors.append(f"Missing quality ratchet artifact: {path.relative_to(ROOT)}")

if config_path.is_file():
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    ruff = config.get("ruff") or {}
    touched = config.get("touched_code") or {}
    mypy = config.get("mypy") or {}
    coverage = config.get("coverage") or {}
    if config.get("version") != 1 or ruff.get("baseline_findings") != 758 or ruff.get("policy") != "never_increase":
        errors.append("Ruff must preserve the measured 758-finding baseline and prohibit debt growth")
    module_budgets = ruff.get("module_budgets") or {}
    project_budget = module_budgets.get("scripts/project_intelligence.py") or {}
    if project_budget.get("current_findings") != 10 or project_budget.get("next_target") != 9:
        errors.append("Project Intelligence Ruff debt must retain its measured current count and lower next target")
    retrieval_budget = module_budgets.get("scripts/retrieval_intelligence.py") or {}
    if retrieval_budget.get("current_findings") != 6 or retrieval_budget.get("next_target") != 5:
        errors.append("Retrieval Intelligence Ruff debt must retain its measured current count and lower next target")
    if "scripts/project_intelligence_promotion.py" not in (mypy.get("modules") or []):
        errors.append("The extracted Project Intelligence promotion module must remain in the zero-error mypy scope")
    if len(mypy.get("modules") or []) < 4 or mypy.get("policy") != "selected_module_ratchet":
        errors.append("Mypy must retain its existing selected-module gradual scope")
    if "scripts/validation_observation.py" not in (mypy.get("modules") or []):
        errors.append("The typed validation observation collector must join the zero-finding mypy modules")
    if coverage.get("policy") != "report_only" or coverage.get("minimum_percent") is not None:
        errors.append("Coverage must remain report-only until module baselines are established")
    storage_coverage = (coverage.get("module_baselines") or {}).get("scripts/project_intelligence_storage.py") or {}
    if storage_coverage.get("evidence") != "tests/evidence/module_extraction_lifecycle.py" or storage_coverage.get("measurement_scope") != "bounded_storage_lifecycle":
        errors.append("Coverage baseline must be bound to the bounded storage lifecycle evidence")
    if ruff.get("report_dimensions") != ["rule", "module", "auto_fixable"]:
        errors.append("Ruff debt report must include rule, module, and auto-fixability dimensions")
    if touched.get("policy") != "no_new_findings" or touched.get("missing_base_behavior") != "block":
        errors.append("Touched Python code must have a base comparison and fail closed when it is unavailable")
    lifecycle = ROOT / "tests/evidence/quality_ratchet_lifecycle.py"
    result = subprocess.run([sys.executable, str(lifecycle)], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        errors.append(f"Quality ratchet lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
