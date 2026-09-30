"""Structural contract tests for Implementation Profile and language profiles."""
from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import implementation_profile_validate as validator

errors: list[str] = []
template = yaml.safe_load((ROOT / "templates/implementation/IMPLEMENTATION_PROFILE.yaml").read_text(encoding="utf-8"))


def expect_error(doc: dict, fragment: str, label: str) -> None:
    result = validator.validate_profile(doc)
    if not any(fragment in message for message in result["errors"]):
        errors.append(label)


blocked = validator.validate_profile(template)
if blocked["structural_status"] != "PASS" or blocked["implementation_status"] != "BLOCKED":
    errors.append(f"unresolved contract authority must be structurally valid and implementation-blocked: {blocked}")

ready = deepcopy(template)
ready["status"] = "READY"
ready["contract"].update({
    "authority": "canonical",
    "resolution": "confirmed",
    "evidence": [{"source": "human", "reference": "approved-contract"}],
})
ready["unresolved"] = []
if validator.validate_profile(ready)["structural_status"] != "PASS":
    errors.append(f"resolved canonical-contract profile should pass: {validator.validate_profile(ready)}")

bad = deepcopy(ready)
bad["ownership"]["generated"] = ["src/client.go"]
bad["ownership"]["project_owned"] = ["src/client.go"]
expect_error(bad, "overlaps", "ownership categories must reject the same path")

bad = deepcopy(ready)
bad["ownership"]["unresolved"] = ["../secrets.env"]
expect_error(bad, "normalized repository-relative", "ownership must reject parent traversal")

bad = deepcopy(ready)
bad["architecture"]["ddd"]["tactical"].update({"level": "none", "resolution": "not_detected"})
expect_error(bad, "not_detected is not none", "not_detected must not be interpreted as none")

bad = deepcopy(ready)
bad["technology"]["language"]["resolution"] = "strong_evidence"
bad["technology"]["language"]["evidence"] = []
expect_error(bad, "evidence is required", "resolved language must retain provenance")

bad = deepcopy(ready)
bad["unresolved"].append({"id": "U1", "topic": "ownership", "description": "Unknown path", "blocking": True, "resolution": "Keep protected", "evidence": []})
if validator.validate_profile(bad)["implementation_status"] != "BLOCKED":
    errors.append("blocking unresolved items must block implementation readiness")

for language in sorted(validator.LANGUAGES):
    path = ROOT / "references/languages" / language / "PROFILE.yaml"
    profile = yaml.safe_load(path.read_text(encoding="utf-8"))
    profile_errors = validator.validate_language_profile(profile)
    if profile_errors:
        errors.extend(f"{language}: {issue}" for issue in profile_errors)

fixture = yaml.safe_load((ROOT / "tests/fixtures/implementation_resolution_scenarios.yaml").read_text(encoding="utf-8"))
cases = fixture.get("scenarios") or []
ids = [row.get("id") for row in cases]
if fixture.get("version") != 1 or len(cases) != 16 or len(set(ids)) != 16:
    errors.append("scenario fixture must contain 16 uniquely identified representative cases")
for row in cases:
    if not isinstance(row.get("context"), str) or not row["context"].strip():
        errors.append(f"scenario {row.get('id')} needs a concrete context")
    if not any(key in row for key in ("must_preserve", "must_not_infer", "must_recommend", "must_require", "must_resolve", "must_block", "must_protect", "must_not_modify", "must_route", "must_record", "must_report", "must_not_report")):
        errors.append(f"scenario {row.get('id')} needs explicit expected behavior")

if errors:
    for error in errors:
        print(f"ERROR: {error}")
else:
    print("Implementation Profile structural contracts PASS; 4 language profiles and 16 decision scenarios validated.")
