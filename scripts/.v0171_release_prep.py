#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def promote_068() -> None:
    path = ROOT / "tests/scenario_coverage.yaml"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(?ms)(  - id: "068"\n    path: tests/scenarios/068-v07-to-v08-harness-migration\.md\n)'
        r'    coverage: manual\n'
        r'    evidence:\n      - tests/scenarios/068-v07-to-v08-harness-migration\.md\n'
        r'(?:    note: [^\n]+\n)?'
    )
    replacement = (
        r'\1'
        '    coverage: lifecycle\n'
        '    evidence:\n'
        '      - tests/evidence/legacy_harness_migration_lifecycle.py\n'
        '      - tests/validate_repository.py\n'
    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Scenario 068 manual registry block not found exactly once")
    path.write_text(updated, encoding="utf-8")


def update_validator() -> None:
    path = ROOT / "tests/validation/conformance_isolation.py"
    text = path.read_text(encoding="utf-8")
    old = '''        if cov.get("manual") != 11 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 43 or cov.get("automated") != 114:\n            errors.append("v0.17.0 baseline must report manual=11, lifecycle=43, agent_eval=52 and automated=114")'''
    new = '''        if cov.get("manual") != 10 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 44 or cov.get("automated") != 115:\n            errors.append("v0.17.1 baseline must report manual=10, lifecycle=44, agent_eval=52 and automated=115")'''
    if old not in text:
        raise RuntimeError("v0.17.0 conformance baseline marker not found")
    text = text.replace(old, new, 1)

    old_eval = 'errors.append("v0.17.0 committed Agent Eval baseline must contain 52 passing case/result pairs")'
    new_eval = 'errors.append("v0.17.1 committed Agent Eval baseline must contain 52 passing case/result pairs")'
    if old_eval not in text:
        raise RuntimeError("v0.17.0 Agent Eval label not found")
    text = text.replace(old_eval, new_eval, 1)

    marker = 'reconciled_contracts = {\n'
    block = '''# v0.17.1 legacy installation -> managed Harness migration lifecycle\nlegacy_harness_migration_evidence = ROOT / "tests/evidence/legacy_harness_migration_lifecycle.py"\nif not legacy_harness_migration_evidence.exists():\n    errors.append("Missing v0.17.1 legacy Harness migration lifecycle evidence")\nelse:\n    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(legacy_harness_migration_evidence)], capture_output=True, text=True)\n    if compiled.returncode != 0:\n        errors.append(f"Legacy Harness migration evidence syntax failed: {compiled.stderr.strip()}")\n    else:\n        result = subprocess.run([sys.executable, str(legacy_harness_migration_evidence)], capture_output=True, text=True)\n        if result.returncode != 0:\n            errors.append(f"Legacy Harness migration lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")\n\n'''
    if marker not in text:
        raise RuntimeError("validator reconciliation insertion marker not found")
    if block not in text:
        text = text.replace(marker, block + marker, 1)
    path.write_text(text, encoding="utf-8")


def update_version() -> None:
    version = ROOT / "VERSION"
    if version.read_text(encoding="utf-8").strip() != "0.17.0":
        raise RuntimeError("v0.17.1 prep requires VERSION 0.17.0 baseline")
    version.write_text("0.17.1\n", encoding="utf-8")


def update_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    section = '''## 0.17.1\n\n### Residual Harness Migration Evidence Maturity\n\n- Add executable lifecycle evidence for legacy AIPS installation migration through preflight into the managed Global Harness model.\n- Verify the old preflight fast-forwards and re-execs the updated CLI, an installed system refreshes managed Harness content, user-owned instructions survive composition, colliding foreign registrations remain CONFLICT/MANUAL, and a plain repository checkout does not register the Global Harness implicitly.\n- Promote Scenario 068 from manual to lifecycle without adding or changing runtime product behavior.\n- Keep the remaining manual Scenarios truthful: visual scenarios still require rendered evidence; API performance requires measured benchmark evidence; 028/054/064/082/087 require additional end-to-end product capabilities or conflict/lazy-loading behavior before promotion.\n- Raise conformance baseline to 125 total / 10 manual / 19 deterministic / 44 lifecycle / 52 agent_eval / 115 automated / 0 uncovered (92.0% automated).\n- Architecture Diagram Impact: N/A — evidence, validation and release metadata only; no runtime topology, Role, Skill, Capability, Approval Gate or Constitution change.\n\n'''
    if "## 0.17.1\n" in text:
        return
    marker = "# Changelog\n\n"
    if not text.startswith(marker):
        raise RuntimeError("CHANGELOG heading marker not found")
    path.write_text(text.replace(marker, marker + section, 1), encoding="utf-8")


def update_conformance() -> None:
    path = ROOT / "docs/CONFORMANCE.md"
    text = path.read_text(encoding="utf-8")
    if "## v0.17.1 Residual Harness Migration Evidence Maturity" in text:
        return
    section = '''\n\n## v0.17.1 Residual Harness Migration Evidence Maturity\n\nPromoted evidence:\n\n~~~text\n068 Legacy Installation to Managed Harness Migration -> Lifecycle\n~~~\n\nScenario 068 now executes two temporary Git-system lifecycles. The installed-system path establishes managed Harness state, performs a remote AIPS update through `preflight`, proves the updated CLI is re-entered, refreshes managed adapter content, preserves pre-existing user instructions, and keeps a colliding foreign Gemini registration as `CONFLICT` / `MANUAL` without overwriting it. The plain-checkout path performs the same update/re-exec flow without an installation marker and proves no Global Harness state is registered implicitly.\n\nResidual manual gap classification:\n\n~~~text\n004                         measured benchmark/profile evidence required\n021 / 022 / 039 / 055       rendered/screenshot visual evidence infrastructure required\n028                         complete staging-to-production delivery lifecycle required\n054                         approval-backed authoritative promotion mutation required\n064                         executable material instruction-conflict surfacing required\n082                         contradictory discovery vs approved override preservation required\n087                         component-targeted monorepo lazy-loading execution required\n~~~\n\nThese remain manual rather than being promoted by partial or semantic-only evidence.\n\nv0.17.1 baseline:\n\n~~~text\nTotal         125\nManual         10\nDeterministic  19\nLifecycle      44\nAgent Eval     52\nAutomated     115\nUncovered       0\nAutomated     92.0%\n~~~\n\nArchitecture Diagram Impact: N/A. This release adds executable evidence and conformance metadata only; it does not change runtime topology, Role, Skill, Capability, Approval Gate, Constitution, or managed Harness behavior.\n'''
    path.write_text(text.rstrip() + section + "\n", encoding="utf-8")


def main() -> int:
    if (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "0.17.1":
        print("v0.17.1 release preparation already applied")
        return 0
    promote_068()
    update_validator()
    update_version()
    update_changelog()
    update_conformance()
    result = subprocess.run([sys.executable, str(ROOT / "tests/validate_repository.py")], cwd=ROOT, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        return result.returncode
    print("v0.17.1 release preparation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
