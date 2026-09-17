#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def promote_082() -> None:
    path = ROOT / "tests/scenario_coverage.yaml"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(?ms)(  - id: "082"\n    path: tests/scenarios/082-project-overrides-survive-refresh\.md\n)'
        r'    coverage: manual\n'
        r'    evidence:\n      - tests/scenarios/082-project-overrides-survive-refresh\.md\n'
        r'(?:    note: [^\n]+\n)?'
    )
    replacement = (
        r'\1'
        '    coverage: lifecycle\n'
        '    evidence:\n'
        '      - tests/evidence/project_override_reconciliation_lifecycle.py\n'
        '      - tests/validate_repository.py\n'
    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Scenario 082 manual registry block not found exactly once")
    path.write_text(updated, encoding="utf-8")


def update_validator() -> None:
    path = ROOT / "tests/validation/conformance_isolation.py"
    text = path.read_text(encoding="utf-8")
    old = '''        if cov.get("manual") != 10 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 44 or cov.get("automated") != 115:\n            errors.append("v0.17.1 baseline must report manual=10, lifecycle=44, agent_eval=52 and automated=115")'''
    new = '''        if cov.get("manual") != 9 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 45 or cov.get("automated") != 116:\n            errors.append("v0.18.0 baseline must report manual=9, lifecycle=45, agent_eval=52 and automated=116")'''
    if old not in text:
        raise RuntimeError("v0.17.1 conformance baseline marker not found")
    text = text.replace(old, new, 1)

    old_eval = 'errors.append("v0.17.1 committed Agent Eval baseline must contain 52 passing case/result pairs")'
    new_eval = 'errors.append("v0.18.0 committed Agent Eval baseline must contain 52 passing case/result pairs")'
    if old_eval not in text:
        raise RuntimeError("v0.17.1 Agent Eval label not found")
    text = text.replace(old_eval, new_eval, 1)

    marker = 'reconciled_contracts = {\n'
    block = '''# v0.18.0 Project Intelligence override reconciliation lifecycle\nproject_override_reconciliation_evidence = ROOT / "tests/evidence/project_override_reconciliation_lifecycle.py"\nif not project_override_reconciliation_evidence.exists():\n    errors.append("Missing v0.18.0 Project Intelligence reconciliation lifecycle evidence")\nelse:\n    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(project_override_reconciliation_evidence)], capture_output=True, text=True)\n    if compiled.returncode != 0:\n        errors.append(f"Project Intelligence reconciliation evidence syntax failed: {compiled.stderr.strip()}")\n    else:\n        result = subprocess.run([sys.executable, str(project_override_reconciliation_evidence)], capture_output=True, text=True)\n        if result.returncode != 0:\n            errors.append(f"Project Intelligence reconciliation lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")\n\n'''
    if marker not in text:
        raise RuntimeError("validator reconciliation insertion marker not found")
    if block not in text:
        text = text.replace(marker, block + marker, 1)
    path.write_text(text, encoding="utf-8")


def update_version() -> None:
    path = ROOT / "VERSION"
    current = path.read_text(encoding="utf-8").strip()
    if current != "0.17.1":
        raise RuntimeError(f"v0.18.0 prep requires VERSION 0.17.1 baseline, found {current}")
    path.write_text("0.18.0\n", encoding="utf-8")


def update_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.18.0\n" in text:
        return
    section = '''## 0.18.0\n\n### Project Intelligence Reconciliation\n\n- Add deterministic `aips intelligence reconcile --discoveries <yaml>` for comparing structured repository discovery candidates with approved Project Intelligence overrides.\n- Evolve newly created `PROJECT_OVERRIDES.yaml` to version 2 with stable subject/scope/value keys while preserving legacy unkeyed entries without guessing their semantics.\n- Preserve approved inferences, additional rules, exceptions and exclusions; matching evidence is aligned, unmatched evidence remains derived, and contradictory evidence becomes a stable `DISCOVERY_OVERRIDE_CONFLICT` instead of overwriting approved state.\n- Persist conflict metadata using stable hashes/pointers rather than duplicating raw discovered values, preserve manually maintained conflicts, and surface open conflicts through status/context/review outputs.\n- Add executable lifecycle evidence proving approved overrides survive contradictory refresh input, scoped exceptions are respected, conflict IDs are deterministic/idempotent, and AIPS-managed conflicts clear when later evidence aligns.\n- Promote Scenario 082 from manual to lifecycle. Remaining manual Scenarios: 004, 021, 022, 028, 039, 054, 055, 064 and 087.\n- Raise conformance baseline to 125 total / 9 manual / 19 deterministic / 45 lifecycle / 52 agent_eval / 116 automated / 0 uncovered (92.8% automated).\n- Architecture Diagram Impact: N/A — behavior is added inside the existing Project Intelligence component; no runtime topology, Role, Skill, Capability boundary, Approval Gate or Constitution change.\n\n'''
    marker = "# Changelog\n\n"
    if not text.startswith(marker):
        raise RuntimeError("CHANGELOG heading marker not found")
    path.write_text(text.replace(marker, marker + section, 1), encoding="utf-8")


def update_conformance() -> None:
    path = ROOT / "docs/CONFORMANCE.md"
    text = path.read_text(encoding="utf-8")
    title = "## v0.18.0 Project Intelligence Reconciliation"
    if title in text:
        return
    section = '''\n\n## v0.18.0 Project Intelligence Reconciliation\n\nPromoted evidence:\n\n~~~text\n082 Project Overrides Survive Refresh -> Lifecycle\n~~~\n\nProject Intelligence now exposes a deterministic reconciliation primitive for structured discovery candidates. `PROJECT_OVERRIDES.yaml` version 2 gives approved decisions stable subject/scope/value keys. Reconciliation preserves approved inference/rule/exception/exclusion lists and never treats newly discovered evidence as permission to overwrite them. Matching evidence is aligned, unmatched evidence remains a derived candidate, and contradictory or explicitly excluded evidence produces a stable `DISCOVERY_OVERRIDE_CONFLICT`.\n\nThe executable lifecycle creates a temporary attached Git project, bootstraps Project Intelligence, establishes approved inference/rule/exception/exclusion decisions plus a manual conflict, and then reconciles aligned, contradictory, scoped and unmatched candidates through the public `aips intelligence reconcile` command. It verifies that approved state remains byte-for-byte equivalent at the semantic list level, scoped exceptions apply to descendant scopes, manual conflicts survive, raw contradictory values are not duplicated into conflict records, review output surfaces the conflict, repeated reconciliation is idempotent, and AIPS-managed conflicts clear when later candidate evidence aligns.\n\nResidual manual gap classification:\n\n~~~text\n004                         measured benchmark/profile evidence required\n021 / 022 / 039 / 055       rendered/screenshot visual evidence infrastructure required\n028                         complete staging-to-production delivery lifecycle required\n054                         approval-backed authoritative promotion mutation required\n064                         executable material runtime/project instruction-conflict surfacing required\n087                         component-targeted monorepo lazy-loading execution required\n~~~\n\nThese remain manual rather than being promoted by adjacent or partial evidence. Scenario 082 is the only Scenario promoted in this release.\n\nv0.18.0 baseline:\n\n~~~text\nTotal         125\nManual          9\nDeterministic  19\nLifecycle      45\nAgent Eval     52\nAutomated     116\nUncovered       0\nAutomated     92.8%\n~~~\n\nArchitecture Diagram Impact: N/A. This release extends behavior inside the existing Project Intelligence component and does not change runtime topology, Role, Skill, Capability boundary, Approval Gate, or Constitution.\n'''
    path.write_text(text.rstrip() + section + "\n", encoding="utf-8")


def main() -> int:
    update_version()
    promote_082()
    update_validator()
    update_changelog()
    update_conformance()
    targeted = subprocess.run([sys.executable, str(ROOT / "tests/evidence/project_override_reconciliation_lifecycle.py")], cwd=ROOT, capture_output=True, text=True)
    print(targeted.stdout)
    print(targeted.stderr, file=sys.stderr)
    if targeted.returncode != 0:
        return targeted.returncode
    full = subprocess.run([sys.executable, str(ROOT / "tests/validate_repository.py")], cwd=ROOT, capture_output=True, text=True)
    print(full.stdout)
    print(full.stderr, file=sys.stderr)
    if full.returncode != 0:
        return full.returncode
    print("v0.18.0 release preparation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
