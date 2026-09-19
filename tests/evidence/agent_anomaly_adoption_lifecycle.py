#!/usr/bin/env python3
from __future__ import annotations

import copy
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import evolution_adoption as adoption  # noqa: E402
from evolution_analysis import canonical_digest  # noqa: E402

BASELINE = ROOT / "references/evolution/ISSUE_79_AGENT_ANOMALY_ADOPTION_BASELINE.yaml"
TRIAL_DECISION = ROOT / "references/evolution/ISSUE_79_AGENT_ANOMALY_TRIAL_DECISION.yaml"
TRIAL_RESULT = ROOT / "references/evolution/ISSUE_79_AGENT_OBSERVABLE_EVENT_TRIAL_RESULT.yaml"
ADOPT_DECISION = ROOT / "references/evolution/ISSUE_79_AGENT_ANOMALY_ADOPTION_DECISION.yaml"
BINDING = ROOT / "references/evolution/ISSUE_79_AGENT_ANOMALY_ADOPTION_BINDING.yaml"
REVIEW = ROOT / "references/evolution/ISSUE_79_AGENT_ANOMALY_SYSTEM_IMPROVEMENT_REVIEW.yaml"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    assert isinstance(value, dict)
    return value


baseline = load(BASELINE)
trial_decision = load(TRIAL_DECISION)
trial_result = load(TRIAL_RESULT)
adopt_decision = load(ADOPT_DECISION)
committed_binding = load(BINDING)
review = load(REVIEW)

bound = adoption.bind_committed(baseline, trial_decision, trial_result, adopt_decision)
assert bound == committed_binding
assert not adoption.validate(bound)
assert bound["adoption"]["binding_mode"] == "COMMITTED_CURRENT_BASELINE_TRIAL"
assert bound["adoption"]["baseline_repository_revision"] == "a92a8d83c4cd6d2a04055312ebfa118d4df39f42"
assert bound["adoption"]["trial_baseline_repository_revision"] == "e5e47b28a524352f7f549b49a40a294ddb50a364"
assert bound["authority"]["code_change_authorized"] is False
assert bound["authority"]["remote_branch_or_pr_authorized"] is False
assert bound["authority"]["merge_authorized"] is False
assert bound["authority"]["release_authorized"] is False

review_core = review["review"]
assert review["review_fingerprint"] == canonical_digest(review_core)
assert review_core["adoption_fingerprint"] == bound["adoption_fingerprint"]
assert review_core["appropriateness"] == "SUITABLE_WITH_BOUNDS"
assert review_core["constitution_impact"] == "NO"
assert review_core["approval"]["status"] == "APPROVED"
assert review_core["approval"]["approved_additional_optimizations"] == []
assert all(item["timing"] != "NOW" for item in review_core["additional_optimizations"])
assert "enable any live production capture hook" in review_core["scope"]["out_of_scope"]

bad_baseline = copy.deepcopy(baseline)
bad_baseline["baseline"]["repository_revision"] = "0" * 40
try:
    adoption.bind_committed(bad_baseline, trial_decision, trial_result, adopt_decision)
except ValueError:
    pass
else:
    raise AssertionError("stale/mismatched current baseline must fail closed")

bad_result = copy.deepcopy(trial_result)
bad_result["status"] = "FAIL"
try:
    adoption.bind_committed(baseline, trial_decision, bad_result, adopt_decision)
except ValueError:
    pass
else:
    raise AssertionError("non-PASS committed Trial must fail closed")

bad_fingerprint = copy.deepcopy(baseline)
bad_fingerprint["trial"]["trial_fingerprint"] = "sha256:" + "0" * 64
try:
    adoption.bind_committed(bad_fingerprint, trial_decision, trial_result, adopt_decision)
except ValueError:
    pass
else:
    raise AssertionError("mismatched Trial fingerprint must fail closed")

bad_authority = copy.deepcopy(trial_result)
bad_authority["authority"]["runtime_enforcement_authorized"] = True
try:
    adoption.bind_committed(baseline, trial_decision, bad_authority, adopt_decision)
except ValueError:
    pass
else:
    raise AssertionError("Trial authority expansion must fail closed")

print("agent anomaly Trial-backed adoption lifecycle: PASS")
