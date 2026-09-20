#!/usr/bin/env python3
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "references/evolution/ISSUE_79_LIFECYCLE_RECONCILIATION.yaml"

doc = yaml.safe_load(DOC.read_text(encoding="utf-8")) or {}
assert doc.get("version") == 1
assert (doc.get("issue") or {}).get("number") == 79
assert (doc.get("baseline") or {}).get("version") == "0.46.0"
assert (doc.get("baseline") or {}).get("original_radar_baseline_status") == "STALE"
outcomes = doc.get("outcomes") or {}
assert outcomes["resource_scoped_agent_authorization"]["state"] == "COVERED"
assert outcomes["out_of_band_agent_anomaly_evidence"]["state"] == "ADOPTED_WITH_BOUNDS"
truth = outcomes["out_of_band_agent_anomaly_evidence"]["current_truth"]
assert truth["live_runtime_execution_verified"] is True
assert truth["runtime_specific_live_capture_verified"] is True
assert truth["live_provider_session_verified"] is False
assert truth["provider_model_execution_verified"] is False
assert truth["runtime_enforced"] is False
assert truth["automatic_remediation"] is False
semantic = outcomes["semantic_intent_governance"]
assert semantic["state"] == "DEFERRED"
assert "fresh current-main" in semantic["next_entry_rule"]
closure = doc.get("closure") or {}
assert closure.get("status") == "READY_TO_CLOSE"
assert closure.get("state_reason") == "completed"
assert closure.get("future_work_requires_fresh_issue") is True
authority = doc.get("authority") or {}
assert authority.get("issue_close_authorized") is True
for key in (
    "semantic_intent_trial_authorized",
    "code_change_authorized_by_reconciliation",
    "runtime_enforcement_authorized",
    "automatic_remediation_authorized",
    "merge_authorized_by_reconciliation",
    "release_authorized_by_reconciliation",
):
    assert authority.get(key) is False
print("Issue #79 lifecycle reconciliation: PASS")
