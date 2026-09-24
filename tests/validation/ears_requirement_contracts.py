from __future__ import annotations

from copy import deepcopy
import sys

import yaml

from .static_contracts import ROOT, errors

sys.path.insert(0, str(ROOT))
from scripts.requirements_traceability import validate  # noqa: E402


template_path = ROOT / "templates/planning-package/REQUIREMENTS.yaml"
template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
if validate(template):
    errors.append("REQUIREMENTS.yaml template must satisfy the traceability contract")

bad_pattern = deepcopy(template)
bad_pattern["requirements"][0]["ears_pattern"] = "vague_event"
if not validate(bad_pattern):
    errors.append("EARS registry must reject an unknown pattern")

pattern_statements = {
    "ubiquitous": "The <system> shall <response>.",
    "event_driven": "When <trigger>, the <system> shall <response>.",
    "state_driven": "While <state>, the <system> shall <response>.",
    "optional_feature": "Where <feature is included>, the <system> shall <response>.",
    "unwanted_behavior": "If <undesired condition>, then the <system> shall <response>.",
    "complex": "While <precondition>, when <trigger>, the <system> shall <response>.",
}
for pattern, statement in pattern_statements.items():
    candidate = deepcopy(template)
    candidate["requirements"][0]["ears_pattern"] = pattern
    candidate["requirements"][0]["statement"] = statement
    if validate(candidate):
        errors.append(f"EARS registry must accept the {pattern} structure")

wrong_form = deepcopy(template)
wrong_form["requirements"][0]["statement"] = "The Account Service shall block sign-in after failures."
if not any("does not match" in error for error in validate(wrong_form)):
    errors.append("EARS registry must reject a declared pattern that does not match its sentence structure")

duplicate_acceptance = deepcopy(template)
duplicate_acceptance["requirements"][1]["acceptance_criteria"][0]["id"] = "AC-001"
if not any("duplicate AC-001" in error for error in validate(duplicate_acceptance)):
    errors.append("EARS registry must reject duplicate acceptance IDs")

missing_verification = deepcopy(template)
missing_verification["requirements"][0]["acceptance_criteria"][0]["verification_method"] = ""
if not any("verification_method" in error for error in validate(missing_verification)):
    errors.append("EARS registry must require an acceptance verification method")

missing_link = deepcopy(template)
missing_link["requirements"][0]["acceptance_criteria"] = []
if not any("acceptance_criteria" in error for error in validate(missing_link)):
    errors.append("EARS registry must reject requirements without linked acceptance criteria")

sample = {
    "version": 1,
    "requirements": [
        {
            "id": "FR-001",
            "kind": "functional",
            "ears_pattern": "event_driven",
            "statement": "When five failed sign-in attempts occur within ten minutes, the Account Service shall block sign-in for thirty minutes.",
            "source": "Accepted product decision",
            "acceptance_criteria": [
                {
                    "id": "AC-001",
                    "observable_result": "The sixth attempt is rejected and the account becomes available after thirty minutes.",
                    "verification_method": "Deterministic integration test using a controlled clock",
                    "evidence_refs": ["tests/account_lockout_test.py"],
                }
            ],
        }
    ],
}
if validate(sample):
    errors.append("EARS registry must accept a bounded, traceable functional requirement")

if not template_path.is_file():
    errors.append("Missing Planning Package requirements template")
