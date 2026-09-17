#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"required marker missing in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_project_intelligence() -> None:
    path = ROOT / "scripts/project_intelligence.py"
    text = path.read_text(encoding="utf-8")
    marker = "\ndef context_manifest(root: Path, runtime: str, prompt: str, explain: bool = False) -> dict[str, Any]:\n"
    helper = '''
def collect_instruction_conflicts(store: Path, registry: dict[str, Any], runtime: str) -> list[dict[str, Any]]:
    aliases: dict[str, dict[str, Any]] = {}
    for source in registry.get("sources") or []:
        if not isinstance(source, dict):
            continue
        if source.get("id"):
            aliases[str(source["id"])] = source
        if source.get("path"):
            aliases[str(source["path"])] = source

    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for origin_name, conflict_path in (
        ("project_overrides", store / "PROJECT_OVERRIDES.yaml"),
        ("project_intelligence", store / "PROJECT_INTELLIGENCE.yaml"),
    ):
        doc = load_yaml(conflict_path, {}) if conflict_path.exists() else {}
        for index, item in enumerate(doc.get("conflicts") or []):
            if not isinstance(item, dict):
                continue
            runtimes = [str(x) for x in (item.get("runtimes") or [])]
            if runtimes and runtime not in runtimes:
                continue
            conflict_id = str(item.get("id") or f"{origin_name}-{index + 1}")
            key = (origin_name, conflict_id)
            if key in seen:
                continue
            seen.add(key)
            resolved_sources: list[dict[str, Any]] = []
            for ref in item.get("sources") or []:
                ref_value = str(ref)
                source = aliases.get(ref_value)
                if source is None:
                    resolved_sources.append({"ref": ref_value, "registered": False})
                    continue
                resolved_sources.append({
                    "ref": ref_value,
                    "registered": True,
                    "id": source.get("id"),
                    "path": source.get("path"),
                    "authority": source.get("authority"),
                    "scope": source.get("scope"),
                    "runtime_native": runtime in (source.get("auto_loaded_by") or []),
                })
            result.append({
                "id": conflict_id,
                "origin": origin_name,
                "material": item.get("material") is True,
                "status": str(item.get("status") or "OPEN").upper(),
                "scope": item.get("scope"),
                "summary": item.get("summary") or item.get("reason"),
                "sources": resolved_sources,
            })
    return result


def unresolved_material_conflicts(conflicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terminal = {"RESOLVED", "CLOSED", "SUPERSEDED", "ACCEPTED"}
    return [
        item for item in conflicts
        if item.get("material") is True
        and str(item.get("status", "OPEN")).upper() not in terminal
    ]

'''
    if "def collect_instruction_conflicts(" not in text:
        if marker not in text:
            raise RuntimeError("context_manifest marker missing")
        text = text.replace(marker, "\n" + helper + "def context_manifest(root: Path, runtime: str, prompt: str, explain: bool = False) -> dict[str, Any]:\n", 1)

    old = '''    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []}) if store.exists() else {"sources": []}
    state = intel.get("state") or {}
'''
    new = '''    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []}) if store.exists() else {"sources": []}
    instruction_conflicts = collect_instruction_conflicts(store, registry, runtime) if store.exists() else []
    open_material_conflicts = unresolved_material_conflicts(instruction_conflicts)
    state = intel.get("state") or {}
'''
    if "instruction_conflicts = collect_instruction_conflicts" not in text:
        if old not in text:
            raise RuntimeError("registry context marker missing")
        text = text.replace(old, new, 1)

    old = '''        if readiness != "READY":
            fail_closed_reasons.append(f"intelligence_readiness_{readiness.lower()}")

    return {
'''
    new = '''        if readiness != "READY":
            fail_closed_reasons.append(f"intelligence_readiness_{readiness.lower()}")
        if open_material_conflicts:
            fail_closed_reasons.append("material_instruction_conflict")

    return {
'''
    if 'fail_closed_reasons.append("material_instruction_conflict")' not in text:
        if old not in text:
            raise RuntimeError("fail-closed marker missing")
        text = text.replace(old, new, 1)

    old = '''        "intelligence": {
            "readiness": readiness,
            "review": state.get("review", "UNREVIEWED"),
            "freshness": fr["status"],
        },
'''
    new = '''        "instruction_resolution": {
            "precedence": [
                "runtime_native_scoped",
                "project_authoritative_scoped",
                "derived_project_intelligence",
            ],
            "authoritative_sources_preserved": True,
            "derived_intelligence_governing": False,
            "conflicts": instruction_conflicts,
            "requires_resolution": bool(open_material_conflicts),
        },
        "intelligence": {
            "readiness": readiness,
            "review": state.get("review", "UNREVIEWED"),
            "freshness": fr["status"],
        },
'''
    if '"instruction_resolution": {' not in text:
        if old not in text:
            raise RuntimeError("instruction-resolution insertion marker missing")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_templates() -> None:
    overrides = ROOT / "templates/intelligence/PROJECT_OVERRIDES.yaml"
    text = overrides.read_text(encoding="utf-8")
    old = "excluded_inferences: []\n\nconflicts: []\n"
    new = '''excluded_inferences: []

conflicts: []
# - id: CONFLICT-001
#   material: true
#   status: OPEN
#   scope: project
#   summary: null
#   sources:
#     - AGENTS.md
#     - docs/ADR-001.md
#   runtimes: []
'''
    if old not in text:
        raise RuntimeError("PROJECT_OVERRIDES conflict marker missing")
    overrides.write_text(text.replace(old, new, 1), encoding="utf-8")

    manifest = ROOT / "templates/intelligence/TURN_CONTEXT_MANIFEST.yaml"
    text = manifest.read_text(encoding="utf-8")
    marker = "\nfreshness:\n  status: UNKNOWN\n"
    block = '''
instruction_resolution:
  precedence:
    - runtime_native_scoped
    - project_authoritative_scoped
    - derived_project_intelligence
  authoritative_sources_preserved: true
  derived_intelligence_governing: false
  conflicts: []
  requires_resolution: false

'''
    if "instruction_resolution:" not in text:
        if marker not in text:
            raise RuntimeError("TURN_CONTEXT_MANIFEST freshness marker missing")
        text = text.replace(marker, "\n" + block + "freshness:\n  status: UNKNOWN\n", 1)
    text = text.replace("fail_policy:\n  mode: soft\n", "fail_policy:\n  mode: soft\n  reasons: []\n", 1)
    manifest.write_text(text, encoding="utf-8")


def patch_lifecycle() -> None:
    path = ROOT / "tests/evidence/intelligence_context_lifecycle.py"
    text = path.read_text(encoding="utf-8")
    marker = "\ndef normal_chat_no_bootstrap(base: Path, env: dict[str, str]) -> None:\n"
    function = '''
def material_instruction_conflict_surface(base: Path, env: dict[str, str]) -> None:
    project = base / "instruction-conflict-project"
    init_repo(project)
    (project / "docs").mkdir()
    (project / "AGENTS.md").write_text(
        "# Project instructions\\nArchitecture changes require ADR alignment.\\n",
        encoding="utf-8",
    )
    (project / "docs" / "ADR-001.md").write_text(
        "# ADR 001\\nOfficial architecture rule.\\n",
        encoding="utf-8",
    )
    (project / "main.py").write_text("print('ok')\\n", encoding="utf-8")
    git(project, "add", "-A")
    git(project, "commit", "-qm", "baseline")

    boot = json_run(
        [sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"],
        env,
    )
    store = Path(boot["store"])
    overrides_path = store / "PROJECT_OVERRIDES.yaml"
    overrides = load_yaml(overrides_path)
    overrides["conflicts"] = [{
        "id": "CONFLICT-ARCH-001",
        "material": True,
        "status": "OPEN",
        "scope": "project",
        "summary": "Runtime-native project instruction and official ADR require explicit reconciliation.",
        "sources": ["AGENTS.md", "docs/ADR-001.md"],
        "runtimes": ["codex"],
    }]
    overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False), encoding="utf-8")

    read_ctx = json_run([
        sys.executable, str(PI), "context",
        "--project", str(project),
        "--runtime", "codex",
        "--prompt", "Explain the current architecture.",
        "--format", "json",
    ], env)
    runtime_native = (read_ctx.get("context") or {}).get("runtime_native", [])
    project_native = (read_ctx.get("context") or {}).get("project_native", [])
    require(str(project / "AGENTS.md") in runtime_native, "runtime-native AGENTS source must be preserved")
    require(str(project / "docs" / "ADR-001.md") in project_native, "official ADR source must be preserved")
    resolution = read_ctx.get("instruction_resolution") or {}
    require(resolution.get("authoritative_sources_preserved") is True, "authoritative sources must be preserved")
    require(resolution.get("derived_intelligence_governing") is False, "derived Intelligence must be non-governing")
    require(resolution.get("precedence") == [
        "runtime_native_scoped",
        "project_authoritative_scoped",
        "derived_project_intelligence",
    ], "instruction precedence contract mismatch")
    require(resolution.get("requires_resolution") is True, "open material conflict must require resolution")
    conflicts = resolution.get("conflicts") or []
    require(len(conflicts) == 1, "exactly one conflict should be surfaced")
    conflict = conflicts[0]
    require(conflict.get("id") == "CONFLICT-ARCH-001", "conflict id mismatch")
    require(conflict.get("material") is True and conflict.get("status") == "OPEN", "conflict state mismatch")
    sources = {item.get("path"): item for item in (conflict.get("sources") or []) if item.get("registered")}
    require("AGENTS.md" in sources and "docs/ADR-001.md" in sources, "conflict must retain both source pointers")
    require(sources["AGENTS.md"].get("runtime_native") is True, "AGENTS must be runtime-native for Codex")
    require(sources["docs/ADR-001.md"].get("runtime_native") is False, "ADR must remain project-authoritative")
    require((read_ctx.get("fail_policy") or {}).get("mode") == "soft", "read-only conflict should remain soft")

    mutate_ctx = json_run([
        sys.executable, str(PI), "context",
        "--project", str(project),
        "--runtime", "codex",
        "--prompt", "Modify the API implementation to follow the architecture rule.",
        "--format", "json",
    ], env)
    fail_policy = mutate_ctx.get("fail_policy") or {}
    require(fail_policy.get("mode") == "closed", "mutation with unresolved material conflict must fail closed")
    require("material_instruction_conflict" in (fail_policy.get("reasons") or []), "material conflict fail reason missing")
    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml")
    require((intel.get("topics") or {}) == {}, "authoritative instruction content must not be copied into derived Intelligence")

'''
    if "def material_instruction_conflict_surface(" not in text:
        if marker not in text:
            raise RuntimeError("normal-chat function marker missing")
        text = text.replace(marker, "\n" + function + "def normal_chat_no_bootstrap(base: Path, env: dict[str, str]) -> None:\n", 1)
    call = "        source_registry_runtime_dedup(base, env)\n"
    if "        material_instruction_conflict_surface(base, env)\n" not in text:
        if call not in text:
            raise RuntimeError("lifecycle call marker missing")
        text = text.replace(call, call + "        material_instruction_conflict_surface(base, env)\n", 1)
    path.write_text(text, encoding="utf-8")


def patch_conformance() -> None:
    registry = ROOT / "tests/scenario_coverage.yaml"
    old = '''  - id: "064"
    path: tests/scenarios/064-runtime-and-project-instruction-composition.md
    coverage: manual
    evidence:
      - tests/scenarios/064-runtime-and-project-instruction-composition.md
    note: "Existing lifecycle evidence covers native/project source composition and deduplication, but material conflict surfacing is not yet directly exercised."
'''
    new = '''  - id: "064"
    path: tests/scenarios/064-runtime-and-project-instruction-composition.md
    coverage: lifecycle
    evidence:
      - tests/evidence/intelligence_context_lifecycle.py
      - scripts/project_intelligence.py
      - tests/validate_repository.py
'''
    replace_required(registry, old, new)

    validator = ROOT / "tests/validation/conformance_isolation.py"
    text = validator.read_text(encoding="utf-8")
    old = '''        if cov.get("manual") != 10 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 44 or cov.get("automated") != 115:
            errors.append("v0.17.1 baseline must report manual=10, lifecycle=44, agent_eval=52 and automated=115")'''
    new = '''        if cov.get("manual") != 9 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 45 or cov.get("automated") != 116:
            errors.append("v0.18.0 baseline must report manual=9, lifecycle=45, agent_eval=52 and automated=116")'''
    if old not in text:
        raise RuntimeError("v0.17.1 baseline marker missing")
    text = text.replace(old, new, 1)
    old_eval = 'errors.append("v0.17.1 committed Agent Eval baseline must contain 52 passing case/result pairs")'
    if old_eval not in text:
        raise RuntimeError("Agent Eval version marker missing")
    text = text.replace(old_eval, 'errors.append("v0.18.0 committed Agent Eval baseline must contain 52 passing case/result pairs")', 1)
    marker = "# v0.17 legacy Project Knowledge migration lifecycle\n"
    block = '''# v0.18.0 runtime/project instruction conflict lifecycle
instruction_context_evidence = ROOT / "tests/evidence/intelligence_context_lifecycle.py"
if not instruction_context_evidence.exists():
    errors.append("Missing v0.18.0 instruction context lifecycle evidence")
else:
    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(instruction_context_evidence)], capture_output=True, text=True)
    if compiled.returncode != 0:
        errors.append(f"Instruction context evidence syntax failed: {compiled.stderr.strip()}")
    else:
        result = subprocess.run([sys.executable, str(instruction_context_evidence)], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"Instruction context lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")

'''
    if block not in text:
        if marker not in text:
            raise RuntimeError("validator evidence marker missing")
        text = text.replace(marker, block + marker, 1)
    validator.write_text(text, encoding="utf-8")


def patch_release() -> None:
    version = ROOT / "VERSION"
    if version.read_text(encoding="utf-8").strip() != "0.17.1":
        raise RuntimeError("v0.18.0 requires v0.17.1 baseline")
    version.write_text("0.18.0\n", encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    section = '''## 0.18.0

### Instruction Conflict Resolution Surface

- Add a structured instruction-resolution surface to Turn Context that preserves runtime-native and project-authoritative sources while keeping derived Project Intelligence explicitly non-governing.
- Surface recorded instruction conflicts from Project Overrides / Project Intelligence with registered source pointers, scope, materiality and status instead of silently discarding either source.
- Fail closed for mutating work when an unresolved material instruction conflict is present; read-only work remains soft while exposing the conflict for human/Agent reconciliation.
- Extend Project Overrides and Turn Context templates with the additive conflict-resolution contract.
- Add executable lifecycle evidence for Scenario 064 and promote it from manual to lifecycle.
- Raise conformance baseline to 125 total / 9 manual / 19 deterministic / 45 lifecycle / 52 agent_eval / 116 automated / 0 uncovered (92.8% automated).
- Architecture Diagram Impact: N/A — context-resolution behavior and schema are extended, but runtime topology, Role, Skill, Capability, Approval Gate and Constitution remain unchanged.

'''
    marker = "# Changelog\n\n"
    if "## 0.18.0\n" not in text:
        if not text.startswith(marker):
            raise RuntimeError("CHANGELOG marker missing")
        changelog.write_text(text.replace(marker, marker + section, 1), encoding="utf-8")

    doc = ROOT / "docs/CONFORMANCE.md"
    text = doc.read_text(encoding="utf-8")
    if "## v0.18.0 Instruction Conflict Resolution Surface" not in text:
        section = '''

## v0.18.0 Instruction Conflict Resolution Surface

Promoted evidence:

~~~text
064 Runtime and Project Instruction Composition -> Lifecycle
~~~

The lifecycle fixture creates runtime-native `AGENTS.md` plus an official project ADR, bootstraps Project Intelligence, records an unresolved material conflict in the existing Project Overrides conflict channel, and resolves Turn Context for Codex. It proves both authoritative sources remain present, conflict source pointers are registered rather than copied, derived Project Intelligence is non-governing, the conflict is surfaced structurally, read-only work remains soft, and mutating work fails closed until the material conflict is reconciled. No deterministic semantic winner is invented.

Residual manual Scenarios:

~~~text
004                         measured benchmark/profile evidence required
021 / 022 / 039 / 055       rendered/screenshot visual evidence infrastructure required
028                         complete staging-to-production delivery lifecycle required
054                         approval-backed authoritative promotion mutation required
082                         contradictory discovery vs approved override preservation required
087                         component-targeted monorepo lazy-loading execution required
~~~

v0.18.0 baseline:

~~~text
Total         125
Manual          9
Deterministic  19
Lifecycle      45
Agent Eval     52
Automated     116
Uncovered       0
Automated     92.8%
~~~

Architecture Diagram Impact: N/A. This release extends context-resolution behavior and additive manifest schema only; it does not change runtime topology, Role, Skill, Capability, Approval Gate or Constitution.
'''
        doc.write_text(text.rstrip() + section + "\n", encoding="utf-8")


def main() -> int:
    patch_project_intelligence()
    patch_templates()
    patch_lifecycle()
    patch_conformance()
    patch_release()
    result = subprocess.run([sys.executable, str(ROOT / "tests/validate_repository.py")], cwd=ROOT, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        return result.returncode
    print("v0.18.0 instruction conflict preparation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
