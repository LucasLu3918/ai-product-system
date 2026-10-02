"""Phase 3 Profile and Integration Gate contract regression checks."""
from __future__ import annotations

import ast
import json
import sys
from copy import deepcopy
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from implementation_profile_validate import validate_profile

errors: list[str] = []
template = yaml.safe_load((ROOT / "templates/implementation/IMPLEMENTATION_PROFILE.yaml").read_text(encoding="utf-8"))


def expect_error(profile: dict, fragment: str, label: str) -> None:
    found = validate_profile(profile)["errors"]
    if not any(fragment in item for item in found):
        errors.append(f"{label}: {found}")


legacy = deepcopy(template)
legacy.pop("enforcement")
if validate_profile(legacy)["structural_status"] != "PASS":
    errors.append("legacy Phase 1/2 Profile without enforcement section must remain readable")

ready = deepcopy(template)
ready["enforcement"].update({"mode": "enforce", "scope_paths": ["src/**"],
                              "language_profile": "references/languages/go/PROFILE.yaml"})
ready["enforcement"]["commands"] = [{"id": "go-test", "argv": ["go", "test", "./..."],
                                       "source": "README.md", "timeout_seconds": 120, "deterministic": False}]
ready["quality"]["project_required"] = [{"id": "go-tests", "command_id": "go-test",
                                            "evidence_report": "evidence/go-tests.json"}]
if validate_profile(ready)["structural_status"] != "PASS":
    errors.append(f"valid Phase 3 extension should pass structure: {validate_profile(ready)['errors']}")

bad = deepcopy(ready)
bad["enforcement"]["scope_paths"] = ["../src/**"]
expect_error(bad, "normalized repository-relative", "scope traversal must fail")

bad = deepcopy(ready)
bad["enforcement"]["commands"][0]["argv"] = "go test ./..."
expect_error(bad, "argv must be a non-empty string list", "shell string must fail")

bad = deepcopy(ready)
bad["enforcement"]["commands"][0]["timeout_seconds"] = 0
expect_error(bad, "timeout_seconds must be 1..900", "unbounded/zero timeout must fail")

bad = deepcopy(ready)
bad["quality"]["project_required"][0]["command_id"] = "invented"
expect_error(bad, "must name an enforcement command", "required quality must resolve a declared command")

bad = deepcopy(ready)
bad["enforcement"]["generation_records"] = [{"path": "src/client.go", "tool": "generator", "version": "1",
                                                 "output_sha256": "invalid", "inputs": []}]
expect_error(bad, "output_sha256 must be sha256", "generated output requires a digest")
expect_error(bad, ".inputs is required", "generated output requires input provenance")

schema = json.loads((ROOT / "templates/implementation/IMPLEMENTATION_ENFORCEMENT_REPORT.schema.json").read_text(encoding="utf-8"))
try:
    Draft202012Validator.check_schema(schema)
except Exception as exc:
    errors.append(f"Phase 3 evidence JSON Schema is invalid: {exc}")

gate = yaml.safe_load((ROOT / "config/integration-gate.yaml").read_text(encoding="utf-8"))
checks = {row["id"]: row for row in gate["checks"]}
if "implementation-enforcement-lifecycle" not in checks:
    errors.append("existing Integration Gate must run Phase 3 lifecycle on relevant changes")

gate_tree = ast.parse((ROOT / "scripts/integration_gate.py").read_text(encoding="utf-8"))
if any(isinstance(node, ast.ImportFrom) and node.module == "implementation_enforcement"
       for node in gate_tree.body):
    errors.append("fast Janitor precheck must not import Phase 3-only dependencies at module load")
gate_helper = next((node for node in gate_tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "implementation_enforcement_check"), None)
if gate_helper is None or not any(isinstance(node, ast.ImportFrom) and node.module == "implementation_enforcement"
                                  for node in ast.walk(gate_helper)):
    errors.append("configured Gate path must still import the Phase 3 inspector")

if errors:
    for error in errors:
        print(f"ERROR: {error}")
else:
    print("Implementation Phase 3 contracts PASS: compatibility, paths, commands, provenance, schema and Gate wiring.")
