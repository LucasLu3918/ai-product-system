from __future__ import annotations

import subprocess
import sys

import yaml

from .static_contracts import ROOT, errors

paths = (
    ROOT / "scripts/evolution_relevance.py",
    ROOT / "config/evolution-relevance-labels.yaml",
    ROOT / "tests/evidence/evolution_relevance_lifecycle.py",
    ROOT / "tests/fixtures/evolution-relevance/labels.yaml",
)
for path in paths:
    if not path.is_file():
        errors.append(f"Missing Evolution relevance evidence artifact: {path.relative_to(ROOT)}")

policy_path = ROOT / "config/evolution-relevance-labels.yaml"
if policy_path.is_file():
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    if policy.get("version") != 1 or policy.get("label_authority") != "human":
        errors.append("Evolution relevance labels must use version 1 and explicit Human authority")
    if policy.get("automatic_policy_changes") is not False or policy.get("labels") != []:
        errors.append("Production labels remain empty until reviewed; automatic policy changes stay disabled")

script_path = ROOT / "scripts/evolution_relevance.py"
if script_path.is_file():
    text = script_path.read_text(encoding="utf-8")
    for token in ("precision", "recall", "UNCERTAIN", "NOT_READY", "selection_policy_changed", "automatic_source_policy_changes_authorized"):
        if token not in text:
            errors.append(f"Evolution relevance evaluator missing contract: {token}")

lifecycle = ROOT / "tests/evidence/evolution_relevance_lifecycle.py"
if lifecycle.is_file():
    result = subprocess.run([sys.executable, str(lifecycle)], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        errors.append(f"Evolution relevance lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
