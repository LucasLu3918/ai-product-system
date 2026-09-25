#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from runtime_policy import validate_policy


def main() -> int:
    errors = []
    policy = yaml.safe_load((ROOT / "config/runtime-policy.yaml").read_text()) or {}
    try:
        validate_policy(policy)
    except Exception as exc:
        errors.append(f"runtime policy invalid: {exc}")
    action_schema = yaml.safe_load((ROOT / "orchestration/schemas/runtime-action.yaml").read_text()) or {}
    if action_schema.get("version") != 1:
        errors.append("Runtime Action schema version must be 1")
    registry = yaml.safe_load((ROOT / "harness/adapters/REGISTRY.yaml").read_text()) or {}
    adapters = registry.get("adapters") or {}
    if (adapters.get("codex") or {}).get("governance_enforcement") != "ADVISORY":
        errors.append("Codex enforcement must remain ADVISORY")
    if (adapters.get("gemini-cli") or {}).get("governance_enforcement") != "TOOL_GUARDED":
        errors.append("Gemini CLI must retain its truthful TOOL_GUARDED declaration")
    if "TOOL_GUARDED" not in str((adapters.get("claude-code") or {}).get("governance_enforcement")):
        errors.append("Claude Code preferred guard capability is missing")
    scenario = ROOT / "tests/scenarios/177-runtime-policy-enforcement.md"
    if not scenario.is_file():
        errors.append("Scenario 177 is missing")
    coverage = yaml.safe_load((ROOT / "tests/scenario_coverage.yaml").read_text()) or {}
    entries = [item for item in coverage.get("scenarios", []) if str(item.get("id")) == "177"]
    if len(entries) != 1 or entries[0].get("path") != "tests/scenarios/177-runtime-policy-enforcement.md":
        errors.append("Scenario 177 coverage mapping must be unique and exact")
    forbidden = ("nemo", "langchain", "openai")
    manifest = (ROOT / "requirements.txt").read_text().lower()
    if any(name in manifest for name in forbidden):
        errors.append("Runtime Policy must not add an LLM/NeMo mandatory dependency")
    docs = (ROOT / "orchestration/RUNTIME_POLICY_ENFORCEMENT.md").read_text()
    for required in ("DENY", "REQUIRE_APPROVAL", "BLOCKED", "sandbox", "action digest", "ADVISORY"):
        if required.lower() not in docs.lower():
            errors.append(f"Runtime Policy documentation is missing {required}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("runtime_policy schema/adapter/docs contract evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
