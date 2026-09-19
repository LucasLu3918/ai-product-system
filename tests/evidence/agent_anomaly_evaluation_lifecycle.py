#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "agent_anomaly_evaluation.py"
PROFILE = ROOT / "tests" / "fixtures" / "agent_anomaly_evaluation" / "profile.yaml"
CORPUS = ROOT / "tests" / "fixtures" / "agent_anomaly_evaluation" / "corpus.yaml"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--format", "json", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


validate = run("validate", "--profile", str(PROFILE), "--corpus", str(CORPUS))
assert validate.returncode == 0, validate.stderr
validate_doc = json.loads(validate.stdout)
assert validate_doc["status"] == "PASS"
assert validate_doc["enforcement"]["runtime_enforced"] is False
assert validate_doc["authority"]["automatic_remediation_authorized"] is False

evaluation = run("evaluate", "--profile", str(PROFILE), "--corpus", str(CORPUS))
assert evaluation.returncode == 0, evaluation.stderr
doc = json.loads(evaluation.stdout)
assert doc["status"] == "PASS"
assert doc["case_count"] == 11
assert doc["metrics"] == {
    "true_positive": 6,
    "false_positive": 0,
    "true_negative": 5,
    "false_negative": 0,
    "precision": 1.0,
    "recall": 1.0,
    "false_positive_rate": 0.0,
    "false_negative_rate": 0.0,
}
assert doc["recommendation"] == "HUMAN_REVIEW_TRIAL_EVIDENCE"
assert doc["enforcement"]["mode"] == "POST_EXECUTION_EVIDENCE"
assert doc["enforcement"]["critical_path"] is False
assert doc["authority"]["runtime_enforcement_authorized"] is False
assert doc["authority"]["merge_authorized"] is False
assert doc["authority"]["release_authorized"] is False

base = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))

with tempfile.TemporaryDirectory(prefix="aips-agent-anomaly-eval-") as tmp:
    root = Path(tmp)

    private_reasoning = copy.deepcopy(base)
    private_reasoning["cases"][0]["event"]["chain_of_thought"] = "private"
    private_path = root / "private.yaml"
    private_path.write_text(yaml.safe_dump(private_reasoning, sort_keys=False), encoding="utf-8")
    private_proc = run("validate", "--profile", str(PROFILE), "--corpus", str(private_path))
    assert private_proc.returncode == 2
    assert "prohibited" in private_proc.stderr

    secret = copy.deepcopy(base)
    secret["cases"][0]["event"]["note"] = "api_key=super-secret-value"
    secret_path = root / "secret.yaml"
    secret_path.write_text(yaml.safe_dump(secret, sort_keys=False), encoding="utf-8")
    secret_proc = run("validate", "--profile", str(PROFILE), "--corpus", str(secret_path))
    assert secret_proc.returncode == 2
    assert "secret-like values" in secret_proc.stderr

    regression = copy.deepcopy(base)
    regression["cases"][0]["expected_anomaly"] = True
    regression["cases"][0]["expected_types"] = ["unauthorized_success"]
    regression_path = root / "regression.yaml"
    regression_path.write_text(yaml.safe_dump(regression, sort_keys=False), encoding="utf-8")
    regression_proc = run("evaluate", "--profile", str(PROFILE), "--corpus", str(regression_path))
    assert regression_proc.returncode == 1
    regression_doc = json.loads(regression_proc.stdout)
    assert regression_doc["status"] == "FAIL"
    assert regression_doc["metrics"]["false_negative"] == 1
    assert regression_doc["recommendation"] == "HOLD"

print("agent anomaly evaluation lifecycle: PASS")
