"""Contract checks for the opt-in generator adapter profile and report."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import implementation_profile_validate

errors: list[str] = []
template = yaml.safe_load((ROOT / "templates/implementation/IMPLEMENTATION_PROFILE.yaml").read_text(encoding="utf-8"))
schema = json.loads((ROOT / "templates/implementation/GENERATOR_ADAPTER_REPORT.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)

legacy_result = implementation_profile_validate.validate_profile(template)
if legacy_result["structural_status"] != "PASS" or template["generation"].get("adapters") != []:
    errors.append("legacy/default Profiles must remain structurally valid with no adapters")

report = {
    "schema_version": 1, "kind": "openapi_generator_adapter", "status": "READY", "mode": "preview",
    "candidate_revision": "a" * 40,
    "profile": {"path": "IMPLEMENTATION_PROFILE.yaml", "before_sha256": "sha256:" + "b" * 64, "after_sha256": "sha256:" + "b" * 64},
    "contract": {"path": "api/openapi.yaml", "sha256": "sha256:" + "c" * 64},
    "generator": {"id": "fixture", "executable": "tools/generator", "executable_sha256": "sha256:" + "d" * 64,
                   "version": "1.0", "argv_sha256": "sha256:" + "e" * 64},
    "inputs": [], "output_dir": "src/generated", "outputs": [], "runs": [], "deterministic": True,
    "determinism_verified": None, "applied": False, "existing_outputs_sha256": {}, "cleanup_pending": False,
    "raw_output_persisted": False, "fingerprint": "sha256:" + "f" * 64,
}
validator = Draft202012Validator(schema)
if list(validator.iter_errors(report)):
    errors.append("well-formed preview report must satisfy the schema")
invalid = dict(report, applied=True)
if not list(validator.iter_errors(invalid)):
    errors.append("preview report must not claim an applied output")
invalid_path = dict(report, output_dir="../escape")
if not list(validator.iter_errors(invalid_path)):
    errors.append("report schema must reject parent traversal paths")
