from __future__ import annotations

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
    mypy = config.get("mypy") or {}
    coverage = config.get("coverage") or {}
    if config.get("version") != 1 or ruff.get("baseline_findings") != 872 or ruff.get("policy") != "never_increase":
        errors.append("Ruff must preserve the measured 872-finding baseline and prohibit debt growth")
    if len(mypy.get("modules") or []) < 4 or mypy.get("policy") != "selected_module_ratchet":
        errors.append("Mypy must retain its existing selected-module gradual scope")
    if coverage.get("policy") != "report_only" or coverage.get("minimum_percent") is not None:
        errors.append("Coverage must remain report-only until module baselines are established")
