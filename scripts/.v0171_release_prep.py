#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_scenario_block(text: str, scenario_id: str, coverage: str, evidence: list[str]) -> str:
    pattern = re.compile(
        rf'(?ms)(  - id: "{re.escape(scenario_id)}"\n    path: [^\n]+\n)'
        r'    coverage: [^\n]+\n'
        r'    evidence:\n(?:      - [^\n]+\n)+'
        r'(?:    note: [^\n]+\n)?'
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"Scenario {scenario_id} registry block not found")
    replacement = match.group(1) + f"    coverage: {coverage}\n    evidence:\n"
    replacement += "".join(f"      - {item}\n" for item in evidence)
    return text[:match.start()] + replacement + text[match.end():]


def update_registry() -> None:
    path = ROOT / "tests/scenario_coverage.yaml"
    text = path.read_text(encoding="utf-8")
    text = replace_scenario_block(
        text,
        "068",
        "lifecycle",
        [
            "tests/evidence/legacy_harness_migration_lifecycle.py",
            "tests/validate_repository.py",
        ],
    )
    path.write_text(text, encoding="utf-8")


def update_validator() -> None:
    path = ROOT / "tests/validation/conformance_isolation.py"
    text = path.read_text(encoding="utf-8")
    old = '''        if cov.get("manual") != 11 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 43 or cov.get("automated") != 114:\n            errors.append("v0.17.0 baseline must report manual=11, lifecycle=43, agent_eval=52 and automated=114")'''
    new = '''        if cov.get("manual") != 10 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 44 or cov.get("automated") != 115:\n            errors.append("v0.17.1 baseline must report manual=10, lifecycle=44, agent_eval=52 and automated=115")'''
    if old not in text and new not in text:
        raise RuntimeError("v0.17.0 conformance baseline marker not found")
    text = text.replace(old, new)

    marker = '# v0.17 legacy Project Knowledge migration lifecycle\n'
    block = '''# v0.17.1 legacy installation to managed Harness migration lifecycle\nlegacy_harness_migration_evidence = ROOT / "tests/evidence/legacy_harness_migration_lifecycle.py"\nif not legacy_harness_migration_evidence.exists():\n    errors.append("Missing v0.17.1 legacy Harness migration lifecycle evidence")\nelse:\n    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(legacy_harness_migration_evidence)], capture_output=True, text=True)\n    if compiled.returncode != 0:\n        errors.append(f"Legacy Harness migration evidence syntax failed: {compiled.stderr.strip()}")\n    else:\n        result = subprocess.run([sys.executable, str(legacy_harness_migration_evidence)], capture_output=True, text=True)\n        if result.returncode != 0:\n            errors.append(f"Legacy Harness migration lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")\n\n'''
    if block not in text:
        if marker not in text:
            raise RuntimeError("v0.17 validator insertion marker not found")
        text = text.replace(marker, block + marker, 1)
    path.write_text(text, encoding="utf-8")


def update_version() -> None:
    (ROOT / "VERSION").write_text("0.17.1\n", encoding="utf-8")


def update_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.17.1\n" in text:
        return
    section = '''## 0.17.1\n\n### Legacy Harness Migration Evidence Maturity\n\n- Add an executable end-to-end lifecycle for Scenario 068 covering installed legacy-system preflight update, re-execution through the updated CLI, and automatic Global Harness refresh only when AIPS installation ownership is present.\n- Verify managed Claude instruction refresh preserves user-owned instruction content while applying the updated AIPS-managed block.\n- Verify an unowned Gemini integration name collision is preserved and surfaced as `CONFLICT` with `MANUAL` capability instead of being overwritten.\n- Verify a plain repository checkout without AIPS installation ownership does not implicitly create or register Global Harness adapters during preflight.\n- Promote Scenario 068 from manual to lifecycle and raise conformance to 125 total / 10 manual / 19 deterministic / 44 lifecycle / 52 agent_eval / 115 automated / 0 uncovered (92.0% automated).\n- Architecture Diagram Impact: N/A — evidence/conformance and release metadata only; no runtime topology, Role, Skill, Capability, Approval Gate or Constitution change.\n\n'''
    marker = "# Changelog\n\n"
    if not text.startswith(marker):
        raise RuntimeError("CHANGELOG heading marker not found")
    path.write_text(text.replace(marker, marker + section, 1), encoding="utf-8")


def update_conformance_doc() -> None:
    path = ROOT / "docs/CONFORMANCE.md"
    text = path.read_text(encoding="utf-8")
    heading = "## v0.17.1 Legacy Harness Migration Evidence Maturity"
    if heading in text:
        return
    section = '''\n\n## v0.17.1 Legacy Harness Migration Evidence Maturity\n\nPromoted evidence:\n\n~~~text\n068 Legacy Installation to Managed Harness Migration -> Lifecycle\n~~~\n\nThe lifecycle fixture creates isolated local Git repositories and runtimes and exercises the complete migration contract without network access. It proves that an installed older AIPS system fast-forwards during preflight, re-enters the updated CLI, refreshes the managed Global Harness because installation ownership exists, and preserves user-owned Claude instructions while updating the AIPS-managed block.\n\nThe same fixture exercises the unsafe path: an existing Gemini integration named `aips-global-harness` without AIPS ownership is left untouched and recorded as `CONFLICT` / `MANUAL`. A separate plain-checkout path proves preflight does not implicitly create Harness state when `system-dir` installation ownership is absent.\n\nThe remaining manual Scenarios are:\n\n~~~text\n004 API Performance\n021 Vague Visual Request\n022 User Assets Banner\n028 Complete Product to Production\n039 Visual Polish Shared Component\n054 Project Intelligence Promotion\n055 V2 Visual Consistency Sweep\n064 Runtime and Project Instruction Composition\n082 Project Overrides Survive Refresh\n087 Monorepo Lazy Intelligence\n~~~\n\nv0.17.1 baseline:\n\n~~~text\nTotal         125\nManual         10\nDeterministic  19\nLifecycle      44\nAgent Eval     52\nAutomated     115\nUncovered       0\nAutomated     92.0%\n~~~\n\nArchitecture Diagram Impact: N/A. This release adds executable evidence and updates conformance metadata only; it does not change runtime topology or governance behavior.\n'''
    path.write_text(text.rstrip() + section + "\n", encoding="utf-8")


def main() -> int:
    if (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "0.17.1":
        print("v0.17.1 release preparation already applied")
        return 0
    update_registry()
    update_validator()
    update_version()
    update_changelog()
    update_conformance_doc()

    result = subprocess.run(
        [sys.executable, str(ROOT / "tests/validate_repository.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        return result.returncode
    print("v0.17.1 release preparation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
