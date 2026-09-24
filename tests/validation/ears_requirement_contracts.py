from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys
import tempfile

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

# Exercise the public command-line contract as used by repository tooling.
with tempfile.TemporaryDirectory(prefix="aips-ears-cli-") as temp_dir:
    registry_path = ROOT / temp_dir / "requirements.yaml"
    cli = [sys.executable, str(ROOT / "scripts/requirements_traceability.py"), str(registry_path), "--format", "json"]

    registry_path.write_text(yaml.safe_dump(template, sort_keys=False), encoding="utf-8")
    valid_run = subprocess.run(cli, capture_output=True, text=True, check=False)
    try:
        valid_report = json.loads(valid_run.stdout)
    except json.JSONDecodeError:
        valid_report = {}
    if valid_run.returncode != 0 or valid_report.get("status") != "PASS":
        errors.append("requirements traceability CLI must report PASS and exit zero for a valid registry")

    invalid_cli_registry = deepcopy(template)
    invalid_cli_registry["requirements"][0]["statement"] = "The Account Service shall block sign-in after failures."
    registry_path.write_text(yaml.safe_dump(invalid_cli_registry, sort_keys=False), encoding="utf-8")
    invalid_run = subprocess.run(cli, capture_output=True, text=True, check=False)
    try:
        invalid_report = json.loads(invalid_run.stdout)
    except json.JSONDecodeError:
        invalid_report = {}
    if invalid_run.returncode == 0 or invalid_report.get("status") != "FAIL":
        errors.append("requirements traceability CLI must report FAIL and exit nonzero for an invalid EARS statement")

if not template_path.is_file():
    errors.append("Missing Planning Package requirements template")
