from __future__ import annotations

import subprocess
import sys

import yaml

from .static_contracts import ROOT, errors

paths = (
    ROOT / "scripts/evolution_relevance.py",
    ROOT / "config/evolution-evaluation.yaml",
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

evaluation_path = ROOT / "config/evolution-evaluation.yaml"
if evaluation_path.is_file():
    policy = yaml.safe_load(evaluation_path.read_text(encoding="utf-8")) or {}
    cohort = policy.get("cohort") or {}
    authority = policy.get("authority") or {}
    if cohort.get("sample_size") != 20 or cohort.get("sampling_method") != "sha256-period-rank":
        errors.append("Evolution monthly Human review must use a deterministic sample of 20")
    if authority.get("automatic_source_weight_changes") is not False or authority.get("automatic_source_enable_disable") is not False:
        errors.append("Evolution evaluation must never authorize automatic source policy changes")

script_path = ROOT / "scripts/evolution_relevance.py"
if script_path.is_file():
    text = script_path.read_text(encoding="utf-8")
    for token in (
        "sample_candidates",
        "AWAITING_HUMAN_LABELS",
        "shortlist_precision",
        "shortlist_recall",
        "actionable_yield",
        "source_yield",
        "UNCERTAIN",
        "NOT_READY",
        "selection_policy_changed",
        "automatic_source_policy_changes_authorized",
    ):
        if token not in text:
            errors.append(f"Evolution relevance evaluator missing contract: {token}")

lifecycle = ROOT / "tests/evidence/evolution_relevance_lifecycle.py"
if lifecycle.is_file():
    result = subprocess.run([sys.executable, str(lifecycle)], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        errors.append(f"Evolution relevance lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
