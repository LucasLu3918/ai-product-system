#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"marker not found in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_project_intelligence() -> None:
    path = ROOT / "scripts/project_intelligence.py"
    text = path.read_text(encoding="utf-8")
    marker = "\ndef context_manifest(root: Path, runtime: str, prompt: str, explain: bool = False) -> dict[str, Any]:\n"
    helper = '''\ndef collect_instruction_conflicts(store: Path, registry: dict[str, Any], runtime: str) -> list[dict[str, Any]]:\n    aliases: dict[str, dict[str, Any]] = {}\n    for source in registry.get("sources") or []:\n        if not isinstance(source, dict):\n            continue\n        if source.get("id"):\n            aliases[str(source["id"])] = source\n        if source.get("path"):\n            aliases[str(source["path"])] = source\n\n    result: list[dict[str, Any]] = []\n    seen: set[tuple[str, str]] = set()\n    for origin_name, conflict_path in (\n        ("project_overrides", store / "PROJECT_OVERRIDES.yaml"),\n        ("project_intelligence", store / "PROJECT_INTELLIGENCE.yaml"),\n    ):\n        doc = load_yaml(conflict_path, {}) if conflict_path.exists() else {}\n        for index, item in enumerate(doc.get("conflicts") or []):\n            if not isinstance(item, dict):\n                continue\n            runtimes = [str(x) for x in (item.get("runtimes") or [])]\n            if runtimes and runtime not in runtimes:\n                continue\n            conflict_id = str(item.get("id") or f"{origin_name}-{index + 1}")\n            key = (origin_name, conflict_id)\n            if key in seen:\n                continue\n            seen.add(key)\n            resolved_sources: list[dict[str, Any]] = []\n            for ref in item.get("sources") or []:\n                ref_value = str(ref)\n                source = aliases.get(ref_value)\n                if source is None:\n                    resolved_sources.append({"ref": ref_value, "registered": False})\n                    continue\n                resolved_sources.append({\n                    "ref": ref_value,\n                    "registered": True,\n                    "id": source.get("id"),\n                    "path": source.get("path"),\n                    "authority": source.get("authority"),\n                    "scope": source.get("scope"),\n                    "runtime_native": runtime in (source.get("auto_loaded_by") or []),\n                })\n            result.append({\n                "id": conflict_id,\n                "origin": origin_name,\n                "material": item.get("material") is True,\n                "status": str(item.get("status") or "OPEN").upper(),\n                "scope": item.get("scope"),\n                "summary": item.get("summary") or item.get("reason"),\n                "sources": resolved_sources,\n            })\n    return result\n\n\ndef unresolved_material_conflicts(conflicts: list[dict[str, Any]]) -> list[dict[str, Any]]:\n    terminal = {"RESOLVED", "CLOSED", "SUPERSEDED", "ACCEPTED"}\n    return [item for item in conflicts if item.get("material") is True and str(item.get("status", "OPEN")).upper() not in terminal]\n\n'''
    if "def collect_instruction_conflicts(" not in text:
        if marker not in text:
            raise RuntimeError("context_manifest marker not found")
        text = text.replace(marker, helper + marker, 1)

    old = '''    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []}) if store.exists() else {"sources": []}\n    state = intel.get("state") or {}\n'''
    new = '''    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []}) if store.exists() else {"sources": []}\n    instruction_conflicts = collect_instruction_conflicts(store, registry, runtime) if store.exists() else []\n    open_material_conflicts = unresolved_material_conflicts(instruction_conflicts)\n    state = intel.get("state") or {}\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif "instruction_conflicts = collect_instruction_conflicts" not in text:
        raise RuntimeError("context registry marker not found")

    old = '''        if readiness != "READY":\n            fail_closed_reasons.append(f"intelligence_readiness_{readiness.lower()}")\n\n    return {\n'''
    new = '''        if readiness != "READY":\n            fail_closed_reasons.append(f"intelligence_readiness_{readiness.lower()}")\n        if open_material_conflicts:\n            fail_closed_reasons.append("material_instruction_conflict")\n\n    return {\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif 'fail_closed_reasons.append("material_instruction_conflict")' not in text:
        raise RuntimeError("fail policy marker not found")

    old = '''        "intelligence": {\n            "readiness": readiness,\n            "review": state.get("review", "UNREVIEWED"),\n            "freshness": fr["status"],\n        },\n'''
    new = '''        "instruction_resolution": {\n            "precedence": [\n                "runtime_native_scoped",\n                "project_authoritative_scoped",\n                "derived_project_intelligence",\n            ],\n            "authoritative_sources_preserved": True,\n            "derived_intelligence_governing": False,\n            "conflicts": instruction_conflicts,\n            "requires_resolution": bool(open_material_conflicts),\n        },\n        "intelligence": {\n            "readiness": readiness,\n            "review": state.get("review", "UNREVIEWED"),\n            "freshness": fr["status"],\n        },\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif '"instruction_resolution": {' not in text:
        raise RuntimeError("instruction resolution insertion marker not found")

    path.write_text(text, encoding="utf-8")


def patch_templates() -> None:
    overrides = ROOT / "templates/intelligence/PROJECT_OVERRIDES.yaml"
    text = overrides.read_text(encoding="utf-8")
    old = "excluded_inferences: []\n\nconflicts: []\n"
    new = '''excluded_inferences: []\n\nconflicts: []\n# - id: CONFLICT-001\n#   material: true\n#   status: OPEN\n#   scope: project\n#   summary: null\n#   sources:\n#     - AGENTS.md\n#     - docs/ADR-001.md\n#   runtimes: []\n'''
    if old in text:
        text = text.replace(old, new, 1)
    overrides.write_text(text, encoding="utf-8")

    manifest = ROOT / "templates/intelligence/TURN_CONTEXT_MANIFEST.yaml"
    text = manifest.read_text(encoding="utf-8")
    marker = "\nfreshness:\n  status: UNKNOWN\n"
    block = '''\ninstruction_resolution:\n  precedence:\n    - runtime_native_scoped\n    - project_authoritative_scoped\n    - derived_project_intelligence\n  authoritative_sources_preserved: true\n  derived_intelligence_governing: false\n  conflicts: []\n  requires_resolution: false\n\n'''
    if "instruction_resolution:" not in text:
        if marker not in text:
            raise RuntimeError("TURN_CONTEXT_MANIFEST freshness marker not found")
        text = text.replace(marker, block + "freshness:\n  status: UNKNOWN\n", 1)
    if "fail_policy:\n  mode: soft\n" in text:
        text = text.replace("fail_policy:\n  mode: soft\n", "fail_policy:\n  mode: soft\n  reasons: []\n", 1)
    manifest.write_text(text, encoding="utf-8")


def patch_lifecycle_evidence() -> None:
    path = ROOT / "tests/evidence/intelligence_context_lifecycle.py"
    text = path.read_text(encoding="utf-8")
    marker = "\ndef normal_chat_no_bootstrap(base: Path, env: dict[str, str]) -> None:\n"
    function = r'''\ndef material_instruction_conflict_surface(base: Path, env: dict[str, str]) -> None:\n    project = base / "instruction-conflict-project"\n    init_repo(project)\n    (project / "docs").mkdir()\n    (project / "AGENTS.md").write_text(\n        "# Project instructions\\nArchitecture changes require ADR alignment.\\n",\n        encoding="utf-8",\n    )\n    (project / "docs" / "ADR-001.md").write_text(\n        "# ADR 001\\nOfficial architecture rule.\\n",\n        encoding="utf-8",\n    )\n    (project / "main.py").write_text("print('ok')\\n", encoding="utf-8")\n    git(project, "add", "-A")\n    git(project, "commit", "-qm", "baseline")\n\n    boot = json_run(\n        [sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"],\n        env,\n    )\n    store = Path(boot["store"])\n    overrides_path = store / "PROJECT_OVERRIDES.yaml"\n    overrides = load_yaml(overrides_path)\n    overrides["conflicts"] = [{\n        "id": "CONFLICT-ARCH-001",\n        "material": True,\n        "status": "OPEN",\n        "scope": "project",\n        "summary": "Runtime-native project instruction and official ADR require explicit reconciliation.",\n        "sources": ["AGENTS.md", "docs/ADR-001.md"],\n        "runtimes": ["codex"],\n    }]\n    overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False), encoding="utf-8")\n\n    read_ctx = json_run(\n        [\n            sys.executable, str(PI), "context",\n            "--project", str(project),\n            "--runtime", "codex",\n            "--prompt", "Explain the current architecture.",\n            "--format", "json",\n        ],\n        env,\n    )\n    runtime_native = (read_ctx.get("context") or {}).get("runtime_native", [])\n    project_native = (read_ctx.get("context") or {}).get("project_native", [])\n    require(str(project / "AGENTS.md") in runtime_native, "runtime-native AGENTS source must be preserved")\n    require(str(project / "docs" / "ADR-001.md") in project_native, "official ADR source must be preserved")\n    resolution = read_ctx.get("instruction_resolution") or {}\n    require(resolution.get("authoritative_sources_preserved") is True, "instruction resolution must preserve authoritative sources")\n    require(resolution.get("derived_intelligence_governing") is False, "derived Intelligence must remain non-governing")\n    require(resolution.get("precedence") == [\n        "runtime_native_scoped",\n        "project_authoritative_scoped",\n        "derived_project_intelligence",\n    ], "instruction precedence contract mismatch")\n    require(resolution.get("requires_resolution") is True, "open material conflict must require resolution")\n    conflicts = resolution.get("conflicts") or []\n    require(len(conflicts) == 1, "exactly one material conflict should be surfaced")\n    conflict = conflicts[0]\n    require(conflict.get("id") == "CONFLICT-ARCH-001", "surfaced conflict id mismatch")\n    require(conflict.get("material") is True and conflict.get("status") == "OPEN", "material conflict state mismatch")\n    resolved = {item.get("path"): item for item in (conflict.get("sources") or []) if item.get("registered")}\n    require("AGENTS.md" in resolved and "docs/ADR-001.md" in resolved, "conflict must retain both registered source pointers")\n    require(resolved["AGENTS.md"].get("runtime_native") is True, "AGENTS must be identified as runtime-native for Codex")\n    require(resolved["docs/ADR-001.md"].get("runtime_native") is False, "ADR must remain project-authoritative context")\n    require((read_ctx.get("fail_policy") or {}).get("mode") == "soft", "read-only conflict surfacing should remain soft")\n\n    mutate_ctx = json_run(\n        [\n            sys.executable, str(PI), "context",\n            "--project", str(project),\n            "--runtime", "codex",\n            "--prompt", "Modify the API implementation to follow the architecture rule.",\n            "--format", "json",\n        ],\n        env,\n    )\n    fail_policy = mutate_ctx.get("fail_policy") or {}\n    require(fail_policy.get("mode") == "closed", "mutating work with an unresolved material conflict must fail closed")\n    require("material_instruction_conflict" in (fail_policy.get("reasons") or []), "material conflict must be an explicit fail-closed reason")\n    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml")\n    require((intel.get("topics") or {}) == {}, "authoritative instruction content must not be copied into derived Intelligence")\n\n'''
    if "def material_instruction_conflict_surface(" not in text:
        if marker not in text:
            raise RuntimeError("normal chat fixture marker not found")
        text = text.replace(marker, function + marker, 1)
    call_marker = "        source_registry_runtime_dedup(base, env)\n"
    if "        material_instruction_conflict_surface(base, env)\n" not in text:
        if call_marker not in text:
            raise RuntimeError("source registry fixture call marker not found")
        text = text.replace(call_marker, call_marker + "        material_instruction_conflict_surface(base, env)\n", 1)
    path.write_text(text, encoding="utf-8")


def patch_conformance() -> None:
    registry = ROOT / "tests/scenario_coverage.yaml"
    text = registry.read_text(encoding="utf-8")
    pattern = re.compile(\n        r'(?ms)(  - id: "064"\\n    path: tests/scenarios/064-runtime-and-project-instruction-composition\\.md\\n)'\n        r'    coverage: manual\\n'\n        r'    evidence:\\n      - tests/scenarios/064-runtime-and-project-instruction-composition\\.md\\n'\n        r'(?:    note: [^\\n]+\\n)?'\n    )
    replacement = (\n        r'\\1'\n        '    coverage: lifecycle\\n'\n        '    evidence:\\n'\n        '      - tests/evidence/intelligence_context_lifecycle.py\\n'\n        '      - scripts/project_intelligence.py\\n'\n        '      - tests/validate_repository.py\\n'\n    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Scenario 064 manual registry block not found exactly once")
    registry.write_text(updated, encoding="utf-8")

    validator = ROOT / "tests/validation/conformance_isolation.py"
    text = validator.read_text(encoding="utf-8")
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
    evidence_marker = "# v0.17 legacy Project Knowledge migration lifecycle\n"
    evidence_block = '''# v0.18.0 runtime/project instruction conflict lifecycle\ninstruction_context_evidence = ROOT / "tests/evidence/intelligence_context_lifecycle.py"\nif not instruction_context_evidence.exists():\n    errors.append("Missing v0.18.0 instruction context lifecycle evidence")\nelse:\n    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(instruction_context_evidence)], capture_output=True, text=True)\n    if compiled.returncode != 0:\n        errors.append(f"Instruction context evidence syntax failed: {compiled.stderr.strip()}")\n    else:\n        result = subprocess.run([sys.executable, str(instruction_context_evidence)], capture_output=True, text=True)\n        if result.returncode != 0:\n            errors.append(f"Instruction context lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")\n\n'''
    if evidence_block not in text:
        if evidence_marker not in text:
            raise RuntimeError("validator evidence insertion marker not found")
        text = text.replace(evidence_marker, evidence_block + evidence_marker, 1)
    validator.write_text(text, encoding="utf-8")


def patch_release_docs() -> None:
    version = ROOT / "VERSION"
    if version.read_text(encoding="utf-8").strip() != "0.17.1":
        raise RuntimeError("v0.18.0 prep requires VERSION 0.17.1 baseline")
    version.write_text("0.18.0\n", encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    section = '''## 0.18.0\n\n### Instruction Conflict Resolution Surface\n\n- Add a structured instruction-resolution surface to Turn Context that preserves runtime-native and project-authoritative sources while keeping derived Project Intelligence explicitly non-governing.\n- Surface recorded instruction conflicts from Project Overrides / Project Intelligence with registered source pointers, scope, materiality and status instead of silently discarding either source.\n- Fail closed for mutating work when an unresolved material instruction conflict is present; read-only work remains soft while exposing the conflict for human/Agent reconciliation.\n- Extend Project Overrides and Turn Context templates with the additive conflict-resolution contract.\n- Add executable lifecycle evidence for Scenario 064 and promote it from manual to lifecycle.\n- Raise conformance baseline to 125 total / 9 manual / 19 deterministic / 45 lifecycle / 52 agent_eval / 116 automated / 0 uncovered (92.8% automated).\n- Architecture Diagram Impact: N/A — context-resolution behavior and schema are extended, but runtime topology, Role, Skill, Capability, Approval Gate and Constitution remain unchanged.\n\n'''
    if "## 0.18.0\n" not in text:
        marker = "# Changelog\n\n"
        if not text.startswith(marker):
            raise RuntimeError("CHANGELOG heading marker not found")
        text = text.replace(marker, marker + section, 1)
        changelog.write_text(text, encoding="utf-8")

    doc = ROOT / "docs/CONFORMANCE.md"
    text = doc.read_text(encoding="utf-8")
    if "## v0.18.0 Instruction Conflict Resolution Surface" not in text:
        section = '''\n\n## v0.18.0 Instruction Conflict Resolution Surface\n\nPromoted evidence:\n\n~~~text\n064 Runtime and Project Instruction Composition -> Lifecycle\n~~~\n\nThe lifecycle fixture now creates runtime-native `AGENTS.md` plus an official project ADR, bootstraps Project Intelligence, records an unresolved material conflict in the existing Project Overrides conflict channel, and resolves Turn Context for Codex. It proves both authoritative sources remain present, conflict source pointers are registered rather than copied, derived Project Intelligence is non-governing, the conflict is surfaced structurally, read-only work remains soft, and mutating work fails closed until the material conflict is reconciled. No deterministic semantic winner is invented.\n\nResidual manual Scenarios after this release:\n\n~~~text\n004                         measured benchmark/profile evidence required\n021 / 022 / 039 / 055       rendered/screenshot visual evidence infrastructure required\n028                         complete staging-to-production delivery lifecycle required\n054                         approval-backed authoritative promotion mutation required\n082                         contradictory discovery vs approved override preservation required\n087                         component-targeted monorepo lazy-loading execution required\n~~~\n\nv0.18.0 baseline:\n\n~~~text\nTotal         125\nManual          9\nDeterministic  19\nLifecycle      45\nAgent Eval     52\nAutomated     116\nUncovered       0\nAutomated     92.8%\n~~~\n\nArchitecture Diagram Impact: N/A. This release extends context-resolution behavior and additive manifest schema only; it does not change runtime topology, Role, Skill, Capability, Approval Gate or Constitution.\n'''
        doc.write_text(text.rstrip() + section + "\n", encoding="utf-8")


def main() -> int:
    patch_project_intelligence()
    patch_templates()
    patch_lifecycle_evidence()
    patch_conformance()
    patch_release_docs()
    result = subprocess.run([sys.executable, str(ROOT / "tests/validate_repository.py")], cwd=ROOT, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        return result.returncode
    print("v0.18.0 instruction conflict preparation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
