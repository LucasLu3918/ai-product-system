from __future__ import annotations

import subprocess
import sys

from .static_contracts import ROOT, errors, load_yaml

REQUIRED = (
    ROOT / "orchestration/AGENT_ANOMALY_EVALUATION.md",
    ROOT / "scripts/agent_anomaly_evaluation.py",
    ROOT / "tests/evidence/agent_anomaly_evaluation_lifecycle.py",
    ROOT / "tests/fixtures/agent_anomaly_evaluation/profile.yaml",
    ROOT / "tests/fixtures/agent_anomaly_evaluation/corpus.yaml",
)

for path in REQUIRED:
    if not path.exists():
        errors.append(f"Agent anomaly evaluation required file missing: {path.relative_to(ROOT)}")

profile_path = ROOT / "tests/fixtures/agent_anomaly_evaluation/profile.yaml"
if profile_path.exists():
    profile = load_yaml(profile_path) or {}
    if profile.get("default_effect") != "DENY":
        errors.append("Agent anomaly evaluation fixture must preserve Resource Authorization default DENY")
    authority = profile.get("authority") or {}
    if any(authority.get(key) is not False for key in (
        "human_approval_granted", "merge_authorized", "release_authorized", "protected_operation_authorized"
    )):
        errors.append("Agent anomaly evaluation fixture must not grant protected authority")

corpus_path = ROOT / "tests/fixtures/agent_anomaly_evaluation/corpus.yaml"
if corpus_path.exists():
    corpus = load_yaml(corpus_path) or {}
    thresholds = corpus.get("thresholds") or {}
    if thresholds != {
        "min_precision": 1.0,
        "min_recall": 1.0,
        "max_false_positive_rate": 0.0,
        "max_false_negative_rate": 0.0,
    }:
        errors.append("Agent anomaly evaluation synthetic baseline thresholds must remain strict")
    if len(corpus.get("cases") or []) != 11:
        errors.append("Agent anomaly evaluation synthetic corpus must contain 11 bounded cases")

script = ROOT / "scripts/agent_anomaly_evaluation.py"
if script.exists():
    compiled = subprocess.run(
        [sys.executable, "-m", "py_compile", str(script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if compiled.returncode != 0:
        errors.append(f"agent anomaly evaluation syntax failed: {compiled.stderr.strip()}")
    text = script.read_text(encoding="utf-8")
    for token in (
        '"mode": "POST_EXECUTION_EVIDENCE"',
        '"runtime_enforced": False',
        '"critical_path": False',
        '"automatic_remediation": False',
        '"automatic_remediation_authorized": False',
        '"HUMAN_REVIEW_TRIAL_EVIDENCE"',
    ):
        if token not in text:
            errors.append(f"agent anomaly evaluation safety contract missing: {token}")

evidence = ROOT / "tests/evidence/agent_anomaly_evaluation_lifecycle.py"
if evidence.exists():
    result = subprocess.run([sys.executable, str(evidence)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        errors.append(f"agent anomaly evaluation lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
