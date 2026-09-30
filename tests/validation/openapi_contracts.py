"""Deterministic contracts for OpenAPI Phase 2 classification and safety."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import openapi_contracts as contracts

errors: list[str] = []
base = {
    "openapi": "3.1.0", "info": {"title": "API", "version": "1"},
    "paths": {"/widgets": {"get": {
        "operationId": "listWidgets",
        "parameters": [{"in": "query", "name": "page", "required": False, "schema": {"type": "integer"}}],
        "responses": {"200": {"description": "OK"}},
    }}},
}


def expect(actual: str, expected: str, label: str) -> None:
    if actual != expected:
        errors.append(f"{label}: expected {expected}, got {actual}")


expect(contracts.compare_specs(base, deepcopy(base))["status"], "NO_CHANGE", "unchanged specs")
added = deepcopy(base)
added["paths"]["/health"] = {"get": {"operationId": "health", "responses": {"200": {"description": "OK"}}}}
expect(contracts.compare_specs(base, added)["status"], "NON_BREAKING", "operation addition")
removed = deepcopy(base)
removed["paths"] = {}
expect(contracts.compare_specs(base, removed)["status"], "BREAKING", "operation removal")
required = deepcopy(base)
required["paths"]["/widgets"]["get"]["parameters"].append(
    {"in": "query", "name": "tenant", "required": True, "schema": {"type": "string"}}
)
expect(contracts.compare_specs(base, required)["status"], "BREAKING", "required parameter addition")
optional = deepcopy(base)
optional["paths"]["/widgets"]["get"]["parameters"].append(
    {"in": "query", "name": "cursor", "required": False, "schema": {"type": "string"}}
)
expect(contracts.compare_specs(base, optional)["status"], "NON_BREAKING", "optional parameter addition")
response = deepcopy(base)
response["paths"]["/widgets"]["get"]["responses"]["200"]["description"] = "Updated description"
expect(contracts.compare_specs(base, response)["status"], "NO_CHANGE", "documentation-only response change")
schema = deepcopy(base)
schema["components"] = {"schemas": {"Widget": {"type": "object"}}}
expect(contracts.compare_specs(base, schema)["status"], "UNKNOWN", "component change")
security = deepcopy(base)
security["security"] = [{"bearerAuth": []}]
expect(contracts.compare_specs(base, security)["status"], "UNKNOWN", "global security change")

if errors:
    for error in errors:
        print(f"ERROR: {error}")
else:
    print("OpenAPI compatibility contracts PASS: additions/removals, conservative unknowns, docs-only changes.")
