#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fix_reconcile_count() -> None:
    path = ROOT / "scripts/project_intelligence.py"
    text = path.read_text(encoding="utf-8")
    old = '''        existing = [item for item in (overrides.get("conflicts") or []) if isinstance(item, dict)]\n        existing_ids = {str(item.get("id")) for item in existing if item.get("id")}\n        for conflict in generated:\n            if conflict["id"] not in existing_ids:\n                existing.append(conflict)\n                existing_ids.add(conflict["id"])\n        overrides["conflicts"] = existing\n        atomic_yaml(overrides_path, overrides)\n\n    active = [item for item in existing if str(item.get("status", "OPEN")).upper() not in {"RESOLVED", "DISMISSED"}]\n    return {\n        "project_id": pid,\n        "mode": mode,\n        "preserved_assertions": preserved_assertions,\n        "discovered_inferences": len(discovered),\n        "new_conflicts": len([item for item in generated if item["id"] in existing_ids]),\n'''
    new = '''        existing = [item for item in (overrides.get("conflicts") or []) if isinstance(item, dict)]\n        existing_ids = {str(item.get("id")) for item in existing if item.get("id")}\n        new_conflicts = 0\n        for conflict in generated:\n            if conflict["id"] not in existing_ids:\n                existing.append(conflict)\n                existing_ids.add(conflict["id"])\n                new_conflicts += 1\n        overrides["conflicts"] = existing\n        atomic_yaml(overrides_path, overrides)\n\n    active = [item for item in existing if str(item.get("status", "OPEN")).upper() not in {"RESOLVED", "DISMISSED"}]\n    return {\n        "project_id": pid,\n        "mode": mode,\n        "preserved_assertions": preserved_assertions,\n        "discovered_inferences": len(discovered),\n        "new_conflicts": new_conflicts,\n'''
    if old not in text:
        raise RuntimeError("reconcile count anchor not found")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_cli_and_evidence() -> None:
    cli = ROOT / "bin/aips"
    text = cli.read_text(encoding="utf-8")
    old = '''  aips intelligence context --runtime <id> [--project <path>] [--prompt <text>]\n  aips intelligence render [--project <path>]\n'''
    new = '''  aips intelligence context --runtime <id> [--project <path>] [--prompt <text>]\n  aips intelligence reconcile-overrides [--project <path>]\n  aips intelligence render [--project <path>]\n'''
    if old not in text:
        raise RuntimeError("CLI usage anchor not found")
    cli.write_text(text.replace(old, new, 1), encoding="utf-8")

    evidence = ROOT / "tests/evidence/project_override_reconciliation_lifecycle.py"
    et = evidence.read_text(encoding="utf-8")
    et = et.replace(
        'PI = ROOT / "scripts" / "project_intelligence.py"\n',
        'PI = ROOT / "scripts" / "project_intelligence.py"\nCLI = ROOT / "bin" / "aips"\n',
        1,
    )
    old_call = '''        again = run([sys.executable, str(PI), "reconcile-overrides", "--project", str(project), "--format", "json"], env)\n        require(again.returncode == 0, "idempotent reconciliation failed")\n        require(len(load_yaml(overrides_path).get("conflicts") or []) == 1, "reconciliation must not duplicate same conflict")\n'''
    new_call = '''        again = run(["bash", str(CLI), "intelligence", "reconcile-overrides", "--project", str(project), "--format", "json"], env)\n        require(again.returncode == 0, f"CLI idempotent reconciliation failed: {again.stdout} {again.stderr}")\n        again_doc = json.loads(again.stdout)\n        require(again_doc.get("new_conflicts") == 0, "second reconciliation must report zero new conflicts")\n        require(len(load_yaml(overrides_path).get("conflicts") or []) == 1, "reconciliation must not duplicate same conflict")\n'''
    if old_call not in et:
        raise RuntimeError("evidence idempotence anchor not found")
    evidence.write_text(et.replace(old_call, new_call, 1), encoding="utf-8")


def promote_082() -> None:
    path = ROOT / "tests/scenario_coverage.yaml"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(?ms)(  - id: "082"\n    path: tests/scenarios/082-project-overrides-survive-refresh\.md\n)'
        r'    coverage: manual\n'
        r'    evidence:\n      - tests/scenarios/082-project-overrides-survive-refresh\.md\n'
        r'    note: [^\n]+\n'
    )
    replacement = (
        r'\1'
        '    coverage: lifecycle\n'
        '    evidence:\n'
        '      - tests/evidence/project_override_reconciliation_lifecycle.py\n'
        '      - scripts/project_intelligence.py\n'
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
    text = text.replace(
        'errors.append("v0.17.1 committed Agent Eval baseline must contain 52 passing case/result pairs")',
        'errors.append("v0.18.0 committed Agent Eval baseline must contain 52 passing case/result pairs")',
        1,
    )

    marker = '# v0.15 canonical identity / resume integrity\n'
    block = '''# v0.18 Project Authority reconciliation lifecycle\nproject_authority_evidence = ROOT / "tests/evidence/project_override_reconciliation_lifecycle.py"\nif not project_authority_evidence.exists():\n    errors.append("Missing v0.18 Project Authority reconciliation lifecycle evidence")\nelse:\n    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(project_authority_evidence)], capture_output=True, text=True)\n    if compiled.returncode != 0:\n        errors.append(f"Project Authority reconciliation evidence syntax failed: {compiled.stderr.strip()}")\n    else:\n        result = subprocess.run([sys.executable, str(project_authority_evidence)], capture_output=True, text=True)\n        if result.returncode != 0:\n            errors.append(f"Project Authority reconciliation lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")\n\n'''
    if marker not in text:
        raise RuntimeError("validator insertion marker not found")
    if block not in text:
        text = text.replace(marker, block + marker, 1)
    path.write_text(text, encoding="utf-8")


def update_release_metadata() -> None:
    version = ROOT / "VERSION"
    if version.read_text(encoding="utf-8").strip() != "0.17.1":
        raise RuntimeError("v0.18.0 prep requires VERSION 0.17.1 baseline")
    version.write_text("0.18.0\n", encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    section = '''## 0.18.0\n\n### Project Authority Reconciliation\n\n- Implement deterministic reconciliation between later structured Project Intelligence discovery and user/project-approved `PROJECT_OVERRIDES.yaml` assertions.\n- Preserve approved inferences, additional rules, exceptions and exclusions across refresh; contradictory structured discovery creates an idempotent `OPEN` authority conflict rather than replacing approved state.\n- Surface active authority conflicts in Turn Context and fail closed for material mutation with `unresolved_authority_conflict`.\n- Add the stable `aips intelligence reconcile-overrides` CLI command and lifecycle evidence covering refresh preservation, contradictory evidence, idempotence, CLI routing and mutation blocking.\n- Promote Scenario 082 from manual to lifecycle. Scenario 064 remains manual because v0.18.0 surfaces registered semantic conflicts but intentionally does not guess arbitrary Markdown conflicts by keyword heuristics.\n- Raise conformance baseline to 125 total / 9 manual / 19 deterministic / 45 lifecycle / 52 agent_eval / 116 automated / 0 uncovered (92.8% automated).\n- Architecture Diagram Impact: N/A — this completes an existing Project Intelligence authority contract; no new Role, Skill, Capability category, Approval Gate, Constitution layer, or runtime topology is introduced.\n\n'''
    marker = "# Changelog\n\n"
    if "## 0.18.0\n" not in text:
        if not text.startswith(marker):
            raise RuntimeError("CHANGELOG heading marker not found")
        changelog.write_text(text.replace(marker, marker + section, 1), encoding="utf-8")

    conformance = ROOT / "docs/CONFORMANCE.md"
    ct = conformance.read_text(encoding="utf-8")
    if "## v0.18.0 Project Authority Reconciliation" not in ct:
        ct = ct.rstrip() + '''\n\n## v0.18.0 Project Authority Reconciliation\n\nPromoted evidence:\n\n~~~text\n082 Project Overrides Survive Refresh -> Lifecycle\n~~~\n\nScenario 082 now executes a temporary Git project lifecycle: bootstrap Project Intelligence, persist approved overrides, advance repository evidence, bootstrap again, prove overrides survive, add later structured semantic discovery, reconcile it, persist a deterministic contradiction conflict, re-run reconciliation through the public CLI without duplication, and prove a mutating Turn Context surfaces the active authority conflict and fails closed.\n\nThe reconciler compares structured discovery assertions (`id` + `value` + evidence) with structured approved assertions. It does not parse arbitrary prose to manufacture semantic contradictions. This keeps Scenario 064 manual until direct material instruction-conflict detection has truthful executable evidence.\n\nv0.18.0 baseline:\n\n~~~text\nTotal         125\nManual          9\nDeterministic   19\nLifecycle       45\nAgent Eval      52\nAutomated      116\nUncovered        0\nAutomated      92.8%\n~~~\n\nArchitecture Diagram Impact: N/A. v0.18.0 implements an already-defined Project Intelligence authority/reconciliation contract and adds no new system topology or governance layer.\n''' + "\n"
        conformance.write_text(ct, encoding="utf-8")


def main() -> int:
    fix_reconcile_count()
    update_cli_and_evidence()
    promote_082()
    update_validator()
    update_release_metadata()
    evidence = ROOT / "tests/evidence/project_override_reconciliation_lifecycle.py"
    subprocess.run([sys.executable, "-m", "py_compile", str(ROOT / "scripts/project_intelligence.py"), str(evidence)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(evidence)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tests/validate_repository.py")], cwd=ROOT, check=True)
    print("v0.18.0 Project Authority release prep: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
