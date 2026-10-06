"""Exercise dependency update classification and validation planning."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/dependency_impact.py"
POLICY = ROOT / "config/dependency-policy.yaml"


def run(*args: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return result, json.loads(result.stdout)


policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
ruff, ruff_report = run("plan", "--ecosystem", "pip", "--name", "ruff")
assert ruff.returncode == 0 and ruff_report["classification"] == "DEV_TOOL"
assert ruff_report["risk"] == "LOW" and "targeted_tool_validation" in ruff_report["recommended_validation_plan"]
assert ruff_report["automatic_merge_authorized"] is False and ruff_report["human_decision_required"] is True

semantic, semantic_report = run("plan", "--ecosystem", "pip", "--name", "sentence-transformers")
assert semantic.returncode == 0 and semantic_report["classification"] == "SEMANTIC_RUNTIME"
assert semantic_report["risk"] == "HIGH"
assert {"retrieval_regression", "semantic_trial"}.issubset(semantic_report["recommended_validation_plan"])

unclassified, unknown = run("plan", "--ecosystem", "pip", "--name", "new-package")
assert unclassified.returncode == 0 and unknown["classification"] == "UNCLASSIFIED"
assert unknown["risk"] == "HIGH" and unknown["human_decision_required"] is True

inventory = ROOT / "tests/fixtures/dependency-impact/inventory.yaml"
report, report_data = run("report", "--input", str(inventory))
assert report.returncode == 0 and report_data["status"] == "READY_FOR_HUMAN_REVIEW"
assert report_data["dependency_count"] == 3
assert len({item["dependency"]["normalized_name"] for item in report_data["items"]}) == 3

invalid_policy = dict(policy)
invalid_policy["automatic_merge_authorized"] = True
with tempfile.TemporaryDirectory() as temporary:
    invalid_path = Path(temporary) / "policy.yaml"
    invalid_path.write_text(yaml.safe_dump(invalid_policy), encoding="utf-8")
    invalid, invalid_report = run("classify", "--ecosystem", "pip", "--name", "ruff", "--policy", str(invalid_path))
assert invalid.returncode != 0 and invalid_report["status"] == "BLOCKED"
print("dependency impact lifecycle: PASS")
