#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROMOTIONS = {
    "002": ("agent_eval", [
        "tests/agent_eval/cases/002-existing-rest-api.yaml",
        "tests/agent_eval/results/002-existing-rest-api.yaml",
        "scripts/agent_eval.py",
    ]),
    "006": ("agent_eval", [
        "tests/agent_eval/cases/006-infrastructure-cost.yaml",
        "tests/agent_eval/results/006-infrastructure-cost.yaml",
        "scripts/agent_eval.py",
    ]),
    "029": ("agent_eval", [
        "tests/agent_eval/cases/029-deployment-units-repository-strategy.yaml",
        "tests/agent_eval/results/029-deployment-units-repository-strategy.yaml",
        "scripts/agent_eval.py",
    ]),
    "043": ("agent_eval", [
        "tests/agent_eval/cases/043-review-learning-feedback.yaml",
        "tests/agent_eval/results/043-review-learning-feedback.yaml",
        "scripts/agent_eval.py",
    ]),
    "052": ("agent_eval", [
        "tests/agent_eval/cases/052-project-intelligence-discovery.yaml",
        "tests/agent_eval/results/052-project-intelligence-discovery.yaml",
        "scripts/agent_eval.py",
    ]),
    "088": ("lifecycle", [
        "tests/evidence/project_knowledge_migration_lifecycle.py",
        "tests/validate_repository.py",
    ]),
}

MANUAL_NOTES = {
    "004": "Requires a reproducible benchmark/profile fixture and measured p95 under stated conditions; semantic-only evidence is insufficient.",
    "028": "Requires an end-to-end executable product-to-production lifecycle including staging, release readiness, promotion and post-production verification; current evidence is partial.",
    "054": "Requires executable approval-to-authoritative-source promotion plus SOURCE_REGISTRY deduplication; current evidence does not exercise the complete mutation lifecycle.",
    "087": "Requires a real monorepo fixture proving target-component plus shared-relationship lazy loading without unrelated application preload; current evidence is incomplete.",
}


def replace_scenario_block(text: str, scenario_id: str, coverage: str | None, evidence: list[str] | None, note: str | None) -> str:
    pattern = re.compile(
        rf'(?ms)(  - id: "{re.escape(scenario_id)}"\n    path: [^\n]+\n)'
        r'    coverage: [^\n]+\n'
        r'    evidence:\n(?:      - [^\n]+\n)+'
        r'(?:    note: [^\n]+\n)?'
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"Scenario {scenario_id} registry block not found")
    prefix = match.group(1)
    old = match.group(0)
    if coverage is None:
        cov_match = re.search(r'    coverage: ([^\n]+)', old)
        coverage = cov_match.group(1) if cov_match else "manual"
    if evidence is None:
        evidence = re.findall(r'      - ([^\n]+)', old)
    replacement = prefix + f"    coverage: {coverage}\n    evidence:\n"
    replacement += "".join(f"      - {item}\n" for item in evidence)
    if note:
        replacement += f'    note: "{note}"\n'
    return text[:match.start()] + replacement + text[match.end():]


def update_registry() -> None:
    path = ROOT / "tests/scenario_coverage.yaml"
    text = path.read_text(encoding="utf-8")
    for sid, (coverage, evidence) in PROMOTIONS.items():
        text = replace_scenario_block(text, sid, coverage, evidence, None)
    for sid, note in MANUAL_NOTES.items():
        text = replace_scenario_block(text, sid, None, None, note)
    path.write_text(text, encoding="utf-8")


def update_validator() -> None:
    path = ROOT / "tests/validation/conformance_isolation.py"
    text = path.read_text(encoding="utf-8")
    old = '''        if cov.get("manual") != 17 or cov.get("agent_eval") != 47 or cov.get("lifecycle") != 42 or cov.get("automated") != 108:\n            errors.append("v0.16.9 baseline must report manual=17, lifecycle=42, agent_eval=47 and automated=108")'''
    new = '''        if cov.get("manual") != 11 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 43 or cov.get("automated") != 114:\n            errors.append("v0.17.0 baseline must report manual=11, lifecycle=43, agent_eval=52 and automated=114")'''
    if old not in text and new not in text:
        raise RuntimeError("v0.16.9 conformance baseline marker not found")
    text = text.replace(old, new)

    old_eval = '''        if summary.get("cases") != 47 or summary.get("results") != 47 or summary.get("passed") != 47 or summary.get("failed") != 0:\n            errors.append("v0.16.9 committed Agent Eval baseline must contain 47 passing case/result pairs")'''
    new_eval = '''        if summary.get("cases") != 52 or summary.get("results") != 52 or summary.get("passed") != 52 or summary.get("failed") != 0:\n            errors.append("v0.17.0 committed Agent Eval baseline must contain 52 passing case/result pairs")'''
    if old_eval not in text and new_eval not in text:
        raise RuntimeError("v0.16.9 Agent Eval baseline marker not found")
    text = text.replace(old_eval, new_eval)

    marker = "reconciled_contracts = {\n"
    block = '''# v0.17 legacy Project Knowledge migration lifecycle\nproject_knowledge_migration_evidence = ROOT / "tests/evidence/project_knowledge_migration_lifecycle.py"\nif not project_knowledge_migration_evidence.exists():\n    errors.append("Missing v0.17 Project Knowledge migration lifecycle evidence")\nelse:\n    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(project_knowledge_migration_evidence)], capture_output=True, text=True)\n    if compiled.returncode != 0:\n        errors.append(f"Project Knowledge migration evidence syntax failed: {compiled.stderr.strip()}")\n    else:\n        result = subprocess.run([sys.executable, str(project_knowledge_migration_evidence)], capture_output=True, text=True)\n        if result.returncode != 0:\n            errors.append(f"Project Knowledge migration lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")\n\n'''
    if block not in text:
        if marker not in text:
            raise RuntimeError("validator reconciliation insertion marker not found")
        text = text.replace(marker, block + marker, 1)
    path.write_text(text, encoding="utf-8")


def update_version() -> None:
    (ROOT / "VERSION").write_text("0.17.0\n", encoding="utf-8")


def update_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## 0.17.0\n" in text:
        return
    section = '''## 0.17.0\n\n### Project / Architecture Lifecycle Evidence Maturity\n\n- Add Agent Eval evidence for brownfield REST change planning, infrastructure cost analysis, Deployment Unit repository strategy, review-learning feedback and evidence-based Project Intelligence discovery.\n- Add executable legacy Project Knowledge migration lifecycle evidence that preserves `.ai/knowledge` as migration evidence while new reusable conclusions write to canonical Project Intelligence and authoritative sources remain pointer-over-copy.\n- Promote Scenarios 002, 006, 029, 043 and 052 to agent_eval, and Scenario 088 to lifecycle.\n- Keep Scenarios 004, 028, 054 and 087 manual because their complete contracts require reproducible performance measurement, full production delivery lifecycle, approval-backed authoritative promotion, or real monorepo lazy-loading evidence respectively.\n- Raise conformance baseline to 125 total / 11 manual / 19 deterministic / 43 lifecycle / 52 agent_eval / 114 automated / 0 uncovered (91.2% automated).\n- Architecture Diagram Impact: N/A — evidence/conformance and release metadata only; no runtime topology, Role, Skill, Capability, Approval Gate or Constitution change.\n\n'''
    if not text.startswith("# Changelog\n\n"):
        raise RuntimeError("CHANGELOG heading marker not found")
    text = text.replace("# Changelog\n\n", "# Changelog\n\n" + section, 1)
    path.write_text(text, encoding="utf-8")


def update_conformance_doc() -> None:
    path = ROOT / "docs/CONFORMANCE.md"
    text = path.read_text(encoding="utf-8")
    if "## v0.17.0 Project / Architecture Lifecycle Evidence Maturity" in text:
        return
    section = '''\n\n## v0.17.0 Project / Architecture Lifecycle Evidence Maturity\n\nPromoted evidence:\n\n~~~text\n002 Existing REST API Change                    -> Agent Eval\n006 Infrastructure Cost                        -> Agent Eval\n029 Deployment Units vs Repository Strategy    -> Agent Eval\n043 Review Learning Feedback                   -> Agent Eval\n052 Project Intelligence Discovery             -> Agent Eval\n088 Legacy Project Knowledge Migration         -> Lifecycle\n~~~\n\nScenarios 002, 006, 029, 043 and 052 use observable Agent Eval responses bound to exact Case SHA-256 fingerprints and deterministic rubrics. Scenario 006 validates that recommendations require runtime-current price verification and explicitly avoids treating recorded fixture prices as current truth.\n\nScenario 088 executes a temporary Git project containing legacy `.ai/knowledge`, bootstraps canonical Project Intelligence, verifies migration provenance and pointer-over-copy authoritative sources, writes new reusable conclusions only to canonical Intelligence, finalizes READY, and confirms legacy knowledge remains byte-for-byte unchanged.\n\nThe following roadmap targets intentionally remain manual:\n\n~~~text\n004 API Performance\n028 Complete Product to Production\n054 Project Intelligence Promotion to Authoritative Source\n087 Monorepo Lazy Intelligence\n~~~\n\nThese scenarios require evidence that the current repository does not yet provide end to end: a reproducible benchmark/profile and measured p95; full staging-to-production lifecycle verification; approval-backed authoritative-source mutation and deduplication; and component-targeted monorepo lazy-loading execution. They remain manual rather than being partially promoted.\n\nv0.17.0 baseline:\n\n~~~text\nTotal         125\nManual         11\nDeterministic  19\nLifecycle      43\nAgent Eval     52\nAutomated     114\nUncovered       0\nAutomated     91.2%\n~~~\n\nArchitecture Diagram Impact: N/A. This release changes evidence, conformance metadata and validation expectations only; it does not change runtime topology, Role, Skill, Capability, Approval Gate, Constitution, or canonical Project Intelligence behavior.\n'''
    path.write_text(text.rstrip() + section + "\n", encoding="utf-8")


def main() -> int:
    if (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "0.17.0":
        print("v0.17.0 release preparation already applied")
        return 0
    update_registry()
    update_validator()
    update_version()
    update_changelog()
    update_conformance_doc()

    result = subprocess.run(
        [sys.executable, str(ROOT / "tests/validate_repository.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        return result.returncode
    print("v0.17.0 release preparation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
