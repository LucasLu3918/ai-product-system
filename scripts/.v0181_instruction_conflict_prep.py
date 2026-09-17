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
    start = text.index("def active_authority_conflicts(")
    end = text.index("\n\ndef reconcile_overrides", start)
    replacement = '''def active_authority_conflicts(
    store: Path,
    intel: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    runtime: str | None = None,
) -> list[dict[str, Any]]:
    intel = intel or {}
    registry = registry or load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []})
    aliases: dict[str, dict[str, Any]] = {}
    for source in registry.get("sources") or []:
        if not isinstance(source, dict):
            continue
        if source.get("id"):
            aliases[str(source["id"])] = source
        if source.get("path"):
            aliases[str(source["path"])] = source

    overrides = load_yaml(store / "PROJECT_OVERRIDES.yaml", {"conflicts": []})
    result: list[dict[str, Any]] = []
    for origin, items in (("project_overrides", overrides.get("conflicts") or []), ("project_intelligence", intel.get("conflicts") or [])):
        for item in items:
            if not isinstance(item, dict):
                continue
            if str(item.get("status", "OPEN")).upper() in {"RESOLVED", "DISMISSED"}:
                continue
            runtimes = [str(value) for value in (item.get("runtimes") or [])]
            if runtime and runtimes and runtime not in runtimes:
                continue
            entry = dict(item)
            entry.setdefault("origin", origin)
            if "sources" in entry:
                resolved_sources: list[dict[str, Any]] = []
                for source_ref in entry.get("sources") or []:
                    ref = str(source_ref)
                    source = aliases.get(ref)
                    if source is None:
                        resolved_sources.append({"ref": ref, "registered": False})
                    else:
                        resolved_sources.append({
                            "ref": ref,
                            "registered": True,
                            "id": source.get("id"),
                            "path": source.get("path"),
                            "authority": source.get("authority"),
                            "scope": source.get("scope"),
                            "runtime_native": bool(runtime and runtime in (source.get("auto_loaded_by") or [])),
                        })
                entry["sources"] = resolved_sources
            result.append(entry)
    return result
'''
    text = text[:start] + replacement + text[end:]
    old = '    authority_conflicts = active_authority_conflicts(store, intel) if store.exists() else []\n'
    new = '    authority_conflicts = active_authority_conflicts(store, intel, registry, runtime) if store.exists() else []\n'
    if old not in text:
        raise RuntimeError("authority conflict context marker missing")
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
            "conflicts": authority_conflicts,
            "requires_resolution": bool(authority_conflicts),
        },
        "intelligence": {
            "readiness": readiness,
            "review": state.get("review", "UNREVIEWED"),
            "freshness": fr["status"],
        },
'''
    if '"instruction_resolution": {' not in text:
        if old not in text:
            raise RuntimeError("instruction resolution insertion marker missing")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_templates() -> None:
    overrides = ROOT / "templates/intelligence/PROJECT_OVERRIDES.yaml"
    text = overrides.read_text(encoding="utf-8")
    old = "conflicts: []\n"
    new = '''conflicts: []
# - id: CONFLICT-001
#   type: instruction_conflict
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
        raise RuntimeError("PROJECT_OVERRIDES conflicts marker missing")
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
            raise RuntimeError("TURN_CONTEXT freshness marker missing")
        text = text.replace(marker, "\n" + block + "freshness:\n  status: UNKNOWN\n", 1)
    if "fail_policy:\n  mode: soft\n" in text:
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
    (project / "AGENTS.md").write_text("# Project instructions\\nArchitecture changes require ADR alignment.\\n", encoding="utf-8")
    (project / "docs" / "ADR-001.md").write_text("# ADR 001\\nOfficial architecture rule.\\n", encoding="utf-8")
    (project / "main.py").write_text("print('ok')\\n", encoding="utf-8")
    git(project, "add", "-A")
    git(project, "commit", "-qm", "baseline")

    boot = json_run([sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"], env)
    store = Path(boot["store"])
    overrides_path = store / "PROJECT_OVERRIDES.yaml"
    overrides = load_yaml(overrides_path)
    overrides["conflicts"] = [{
        "id": "CONFLICT-ARCH-001",
        "type": "instruction_conflict",
        "material": True,
        "status": "OPEN",
        "scope": "project",
        "summary": "Runtime-native project instruction and official ADR require explicit reconciliation.",
        "sources": ["AGENTS.md", "docs/ADR-001.md"],
        "runtimes": ["codex"],
    }]
    overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False), encoding="utf-8")

    read_ctx = json_run([
        sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex",
        "--prompt", "Explain the current architecture.", "--format", "json",
    ], env)
    runtime_native = (read_ctx.get("context") or {}).get("runtime_native", [])
    project_native = (read_ctx.get("context") or {}).get("project_native", [])
    require(str(project / "AGENTS.md") in runtime_native, "runtime-native AGENTS source must be preserved")
    require(str(project / "docs" / "ADR-001.md") in project_native, "official ADR source must be preserved")
    resolution = read_ctx.get("instruction_resolution") or {}
    require(resolution.get("authoritative_sources_preserved") is True, "authoritative sources must be preserved")
    require(resolution.get("derived_intelligence_governing") is False, "derived Intelligence must be non-governing")
    require(resolution.get("precedence") == ["runtime_native_scoped", "project_authoritative_scoped", "derived_project_intelligence"], "precedence mismatch")
    require(resolution.get("requires_resolution") is True, "material conflict must require resolution")
    conflicts = resolution.get("conflicts") or []
    require(len(conflicts) == 1 and conflicts[0].get("id") == "CONFLICT-ARCH-001", "material conflict must be surfaced")
    sources = {item.get("path"): item for item in (conflicts[0].get("sources") or []) if item.get("registered")}
    require("AGENTS.md" in sources and "docs/ADR-001.md" in sources, "both authoritative source pointers must be preserved")
    require(sources["AGENTS.md"].get("runtime_native") is True, "AGENTS must be runtime-native for Codex")
    require(sources["docs/ADR-001.md"].get("runtime_native") is False, "ADR must remain project-authoritative")
    require((read_ctx.get("fail_policy") or {}).get("mode") == "soft", "read-only conflict resolution must remain soft")

    claude_ctx = json_run([
        sys.executable, str(PI), "context", "--project", str(project), "--runtime", "claude-code",
        "--prompt", "Explain the current architecture.", "--format", "json",
    ], env)
    require((claude_ctx.get("instruction_resolution") or {}).get("conflicts") == [], "runtime-scoped Codex conflict must not leak into Claude context")

    mutate_ctx = json_run([
        sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex",
        "--prompt", "Modify the API implementation to follow the architecture rule.", "--format", "json",
    ], env)
    fail_policy = mutate_ctx.get("fail_policy") or {}
    require(fail_policy.get("mode") == "closed", "mutation with unresolved authority conflict must fail closed")
    require("unresolved_authority_conflict" in (fail_policy.get("reasons") or []), "authority conflict fail reason missing")
    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml")
    require((intel.get("topics") or {}) == {}, "authoritative instructions must not be copied into derived Intelligence")

'''
    if "def material_instruction_conflict_surface(" not in text:
        if marker not in text:
            raise RuntimeError("normal-chat marker missing")
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
    old = '''        if cov.get("manual") != 9 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 45 or cov.get("automated") != 116:
            errors.append("v0.18.0 baseline must report manual=9, lifecycle=45, agent_eval=52 and automated=116")'''
    new = '''        if cov.get("manual") != 8 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 46 or cov.get("automated") != 117:
            errors.append("v0.18.1 baseline must report manual=8, lifecycle=46, agent_eval=52 and automated=117")'''
    if old not in text:
        raise RuntimeError("v0.18.0 conformance baseline marker missing")
    text = text.replace(old, new, 1)
    old_eval = 'errors.append("v0.18.0 committed Agent Eval baseline must contain 52 passing case/result pairs")'
    if old_eval not in text:
        raise RuntimeError("Agent Eval baseline marker missing")
    text = text.replace(old_eval, 'errors.append("v0.18.1 committed Agent Eval baseline must contain 52 passing case/result pairs")', 1)
    marker = "# v0.18 Project Authority reconciliation lifecycle\n"
    block = '''# v0.18.1 runtime/project instruction composition lifecycle
instruction_context_evidence = ROOT / "tests/evidence/intelligence_context_lifecycle.py"
if not instruction_context_evidence.exists():
    errors.append("Missing v0.18.1 instruction composition lifecycle evidence")
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
            raise RuntimeError("v0.18 authority evidence marker missing")
        text = text.replace(marker, block + marker, 1)
    validator.write_text(text, encoding="utf-8")


def patch_release() -> None:
    version = ROOT / "VERSION"
    if version.read_text(encoding="utf-8").strip() != "0.18.0":
        raise RuntimeError("v0.18.1 requires v0.18.0 baseline")
    version.write_text("0.18.1\n", encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    section = '''## 0.18.1

### Runtime / Project Instruction Conflict Composition

- Extend the v0.18.0 Project Authority conflict pipeline to runtime/project instruction conflicts instead of introducing a parallel conflict engine.
- Resolve conflict source references through `SOURCE_REGISTRY.yaml`, preserve both runtime-native and project-authoritative pointers, and expose runtime-scoped conflicts only to applicable runtimes.
- Add an additive `instruction_resolution` Turn Context surface with explicit precedence and a non-governing derived Project Intelligence guarantee.
- Keep the existing v0.18.0 fail-closed `unresolved_authority_conflict` behavior for mutating work while read-only inspection remains soft.
- Add executable lifecycle evidence and promote Scenario 064 from manual to lifecycle.
- Raise conformance baseline to 125 total / 8 manual / 19 deterministic / 46 lifecycle / 52 agent_eval / 117 automated / 0 uncovered (93.6% automated).
- Architecture Diagram Impact: N/A — this extends the existing Project Authority/context-resolution contract; no runtime topology, Role, Skill, Capability category, Approval Gate or Constitution change.

'''
    marker = "# Changelog\n\n"
    if "## 0.18.1\n" not in text:
        if not text.startswith(marker):
            raise RuntimeError("CHANGELOG marker missing")
        changelog.write_text(text.replace(marker, marker + section, 1), encoding="utf-8")

    doc = ROOT / "docs/CONFORMANCE.md"
    text = doc.read_text(encoding="utf-8")
    if "## v0.18.1 Runtime / Project Instruction Conflict Composition" not in text:
        section = '''

## v0.18.1 Runtime / Project Instruction Conflict Composition

Promoted evidence:

~~~text
064 Runtime and Project Instruction Composition -> Lifecycle
~~~

The lifecycle fixture uses the same Project Authority conflict channel introduced in v0.18.0. It creates runtime-native `AGENTS.md` and an official ADR, records an unresolved material instruction conflict with source pointers and runtime scope, and resolves Turn Context for Codex. The evidence proves both sources remain present, `SOURCE_REGISTRY.yaml` resolves their authority/runtime visibility without copying content, derived Project Intelligence remains non-governing, precedence is explicit, runtime scoping prevents conflict leakage to another runtime, read-only work remains soft, and mutating work continues to fail closed through `unresolved_authority_conflict`. No semantic winner is invented automatically.

Residual manual Scenarios:

~~~text
004                         measured benchmark/profile evidence required
021 / 022 / 039 / 055       rendered/screenshot visual evidence infrastructure required
028                         complete staging-to-production delivery lifecycle required
054                         approval-backed authoritative promotion mutation required
087                         component-targeted monorepo lazy-loading execution required
~~~

v0.18.1 baseline:

~~~text
Total         125
Manual          8
Deterministic  19
Lifecycle      46
Agent Eval     52
Automated     117
Uncovered       0
Automated     93.6%
~~~

Architecture Diagram Impact: N/A. This release extends the existing Project Authority/context-resolution contract only; it introduces no runtime topology, Role, Skill, Capability category, Approval Gate or Constitution change.
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
    print("v0.18.1 instruction conflict integration: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
