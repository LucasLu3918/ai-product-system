from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from project_governance_mode import ENFORCEABLE_ACTIONS, MODES, SCHEMA_VERSION


def main() -> int:
    errors: list[str] = []
    guard = (ROOT / "scripts/governance_guard.py").read_text(encoding="utf-8")
    mode = (ROOT / "scripts/project_governance_mode.py").read_text(encoding="utf-8")
    dispatch = (ROOT / "scripts/aips_cli/dispatch.sh").read_text(encoding="utf-8")
    scenario = ROOT / "tests/scenarios/275-optional-project-governance-modes.md"
    docs = [
        ROOT / "docs/ARCHITECTURE.md",
        ROOT / "docs/human/ARCHITECTURE_OVERVIEW.md",
        ROOT / "docs/human/INSTALLATION.md",
        ROOT / "docs/human/SECURITY_ASSURANCE.md",
        ROOT / "docs/human/USER_GUIDE.md",
        ROOT / "docs/human/CONFORMANCE.md",
        ROOT / "orchestration/CONFORMANCE.md",
        ROOT / "orchestration/RUNTIME_POLICY_ENFORCEMENT.md",
    ]

    if MODES != {"off", "observe", "assist", "enforce"} or SCHEMA_VERSION != 1:
        errors.append("project modes must retain the four-state version-1 contract")
    if not ENFORCEABLE_ACTIONS or "enforce mode requires an explicit action scope" not in mode:
        errors.append("enforce mode must require a non-empty allowlisted action scope")
    if '"mode": "off"' not in mode or '"enforce_scope": []' not in mode:
        errors.append("missing user configuration must resolve to off with no scope")
    if "config_root / \"aips\" / \"projects\"" not in mode:
        errors.append("mode configuration must remain in user-level external storage")
    if '"hookEventName": "PreToolUse"' in guard and "additionalContext" not in guard:
        errors.append("Claude advisories must use the native PreToolUse context envelope")
    if "_GLOBAL_HIGH_ASSURANCE" not in guard or 'global_mode == "high_assurance"' not in guard:
        errors.append("project modes must not bypass the independent global high-assurance policy")
    if guard.index('_HOOK_PHASE = "runtime_policy"') > guard.index("resolve_project_mode(cwd)"):
        errors.append("independent runtime policy must run before project-mode relaxation")
    if '"permissionDecision": "deny"' in guard[guard.index("def emit_mode_advisory"):guard.index("def _hook_impl")]:
        errors.append("advisory envelopes must not deny host permission")
    if '"decision": "allow"' in guard[guard.index("def emit_mode_advisory"):guard.index("def _hook_impl")]:
        errors.append("advisory envelopes must not grant host permission")
    if "mode)" not in dispatch or "project_mode \"$@\"" not in dispatch:
        errors.append("the public Project CLI must route the mode command")
    if not scenario.is_file():
        errors.append("Scenario 275 must be present")
    for path in docs:
        if "off" not in path.read_text(encoding="utf-8").lower():
            errors.append(f"mode contract is missing from {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: optional project governance mode contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
