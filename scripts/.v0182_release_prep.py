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
        raise RuntimeError(f"marker not found in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_project_intelligence() -> None:
    path = ROOT / "scripts/project_intelligence.py"
    text = path.read_text(encoding="utf-8")

    marker = "\ndef context_manifest(root: Path, runtime: str, prompt: str, explain: bool = False) -> dict[str, Any]:\n"
    resolver = '''\ndef resolve_component_context(store: Path, intel: dict[str, Any], component: str | None) -> tuple[dict[str, Any], list[str]]:\n    components = intel.get("components") or {}\n    relationships = intel.get("shared_relationships") or {}\n    public: dict[str, Any] = {\n        "requested": component,\n        "resolved": False,\n        "system_summary": (intel.get("architecture") or {}).get("summary"),\n        "target": None,\n        "shared_relationships": [],\n        "excluded_components": [],\n    }\n    if not component:\n        return public, []\n    target = components.get(component)\n    if not isinstance(target, dict):\n        raise RuntimeError(f"Unknown Project Intelligence component: {component}")\n\n    loaded_paths: list[str] = []\n    target_topics: list[str] = []\n    for value in target.get("topics") or []:\n        topic_path = store / str(value)\n        if not topic_path.is_file():\n            raise RuntimeError(f"Component topic is missing: {value}")\n        absolute = str(topic_path)\n        target_topics.append(absolute)\n        loaded_paths.append(absolute)\n\n    shared: list[dict[str, Any]] = []\n    for relationship_id in target.get("shared_relationships") or []:\n        relationship = relationships.get(str(relationship_id))\n        if not isinstance(relationship, dict):\n            raise RuntimeError(f"Unknown shared relationship for component {component}: {relationship_id}")\n        relationship_path = relationship.get("path")\n        if not relationship_path:\n            raise RuntimeError(f"Shared relationship has no path: {relationship_id}")\n        absolute_path = store / str(relationship_path)\n        if not absolute_path.is_file():\n            raise RuntimeError(f"Shared relationship topic is missing: {relationship_path}")\n        absolute = str(absolute_path)\n        loaded_paths.append(absolute)\n        shared.append({\n            "id": str(relationship_id),\n            "path": absolute,\n            "components": [str(value) for value in (relationship.get("components") or [])],\n        })\n\n    public.update({\n        "resolved": True,\n        "target": {\n            "id": component,\n            "root": target.get("root"),\n            "topics": target_topics,\n        },\n        "shared_relationships": shared,\n        "excluded_components": sorted(str(key) for key in components if str(key) != component),\n    })\n    return public, list(dict.fromkeys(loaded_paths))\n\n\ndef context_manifest(root: Path, runtime: str, prompt: str, explain: bool = False, component: str | None = None) -> dict[str, Any]:\n'''
    if marker not in text:
        raise RuntimeError("context_manifest marker not found")
    text = text.replace(marker, resolver, 1)

    old = '''    available = intel.get("topics") or {}\n    selected: list[str] = []\n    for name in desired_topics:\n        topic = available.get(name)\n        if isinstance(topic, dict) and topic.get("path"):\n            selected.append(str(store / topic["path"]))\n'''
    new = '''    available = intel.get("topics") or {}\n    selected: list[str] = []\n    for name in desired_topics:\n        topic = available.get(name)\n        if isinstance(topic, dict) and topic.get("path"):\n            selected.append(str(store / topic["path"]))\n\n    component_resolution, component_paths = resolve_component_context(store, intel, component)\n    selected = list(dict.fromkeys([*selected, *component_paths]))\n'''
    if old not in text:
        raise RuntimeError("selected topic marker not found")
    text = text.replace(old, new, 1)

    old = '''        "intelligence": {\n            "readiness": readiness,\n'''
    new = '''        "component_resolution": component_resolution,\n        "intelligence": {\n            "readiness": readiness,\n'''
    if old not in text:
        raise RuntimeError("return intelligence marker not found")
    text = text.replace(old, new, 1)

    old = '''    p.add_argument("--prompt", default="")\n    p.add_argument("--format", choices=["yaml", "json"], default="yaml")\n    p.add_argument("--explain", action="store_true")\n'''
    new = '''    p.add_argument("--prompt", default="")\n    p.add_argument("--component")\n    p.add_argument("--format", choices=["yaml", "json"], default="yaml")\n    p.add_argument("--explain", action="store_true")\n'''
    if old not in text:
        raise RuntimeError("context CLI marker not found")
    text = text.replace(old, new, 1)

    old = '            result = context_manifest(root, args.runtime, args.prompt, args.explain)\n'
    new = '            result = context_manifest(root, args.runtime, args.prompt, args.explain, args.component)\n'
    if old not in text:
        raise RuntimeError("context invocation marker not found")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def update_templates() -> None:
    pi = ROOT / "templates/intelligence/PROJECT_INTELLIGENCE.yaml"
    text = pi.read_text(encoding="utf-8")
    marker = "canonical_artifacts: {}\n"
    addition = '''components: {}\n# api:\n#   root: apps/api\n#   topics:\n#     - topics/components/api.md\n#   shared_relationships:\n#     - auth-contract\n\nshared_relationships: {}\n# auth-contract:\n#   path: topics/shared/auth-contract.md\n#   components:\n#     - api\n#     - admin\n\ncanonical_artifacts: {}\n'''
    if marker not in text:
        raise RuntimeError("PROJECT_INTELLIGENCE template marker not found")
    pi.write_text(text.replace(marker, addition, 1), encoding="utf-8")

    turn = ROOT / "templates/intelligence/TURN_CONTEXT_MANIFEST.yaml"
    text = turn.read_text(encoding="utf-8")
    marker = "\ninstruction_resolution:\n"
    addition = '''\ncomponent_resolution:\n  requested: null\n  resolved: false\n  system_summary: null\n  target: null\n  shared_relationships: []\n  excluded_components: []\n\ninstruction_resolution:\n'''
    if marker not in text:
        raise RuntimeError("TURN_CONTEXT template marker not found")
    turn.write_text(text.replace(marker, addition, 1), encoding="utf-8")


def promote_scenario() -> None:
    path = ROOT / "tests/scenario_coverage.yaml"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(?ms)(  - id: "087"\n    path: tests/scenarios/087-monorepo-lazy-intelligence\.md\n)'
        r'    coverage: manual\n'
        r'    evidence:\n      - tests/scenarios/087-monorepo-lazy-intelligence\.md\n'
        r'(?:    note: [^\n]+\n)?'
    )
    replacement = (
        r'\1'
        '    coverage: lifecycle\n'
        '    evidence:\n'
        '      - tests/evidence/monorepo_lazy_intelligence_lifecycle.py\n'
        '      - scripts/project_intelligence.py\n'
        '      - tests/validate_repository.py\n'
    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Scenario 087 manual block not found exactly once")
    path.write_text(updated, encoding="utf-8")


def update_validator() -> None:
    path = ROOT / "tests/validation/conformance_isolation.py"
    text = path.read_text(encoding="utf-8")
    old = '''        if cov.get("manual") != 8 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 46 or cov.get("automated") != 117:\n            errors.append("v0.18.1 baseline must report manual=8, lifecycle=46, agent_eval=52 and automated=117")'''
    new = '''        if cov.get("manual") != 7 or cov.get("agent_eval") != 52 or cov.get("lifecycle") != 47 or cov.get("automated") != 118:\n            errors.append("v0.18.2 baseline must report manual=7, lifecycle=47, agent_eval=52 and automated=118")'''
    if old not in text:
        raise RuntimeError("v0.18.1 baseline marker not found")
    text = text.replace(old, new, 1)
    text = text.replace(
        'errors.append("v0.18.1 committed Agent Eval baseline must contain 52 passing case/result pairs")',
        'errors.append("v0.18.2 committed Agent Eval baseline must contain 52 passing case/result pairs")',
        1,
    )
    marker = "# v0.18.1 runtime/project instruction composition lifecycle\n"
    block = '''# v0.18.2 monorepo lazy component Intelligence lifecycle\nmonorepo_lazy_evidence = ROOT / "tests/evidence/monorepo_lazy_intelligence_lifecycle.py"\nif not monorepo_lazy_evidence.exists():\n    errors.append("Missing v0.18.2 monorepo lazy Intelligence lifecycle evidence")\nelse:\n    compiled = subprocess.run([sys.executable, "-m", "py_compile", str(monorepo_lazy_evidence)], capture_output=True, text=True)\n    if compiled.returncode != 0:\n        errors.append(f"Monorepo lazy Intelligence evidence syntax failed: {compiled.stderr.strip()}")\n    else:\n        result = subprocess.run([sys.executable, str(monorepo_lazy_evidence)], capture_output=True, text=True)\n        if result.returncode != 0:\n            errors.append(f"Monorepo lazy Intelligence lifecycle evidence failed: {result.stdout.strip()} {result.stderr.strip()}")\n\n'''
    if marker not in text:
        raise RuntimeError("validator insertion marker not found")
    text = text.replace(marker, block + marker, 1)
    path.write_text(text, encoding="utf-8")


def update_release_docs() -> None:
    version = ROOT / "VERSION"
    if version.read_text(encoding="utf-8").strip() != "0.18.1":
        raise RuntimeError("v0.18.2 prep requires VERSION 0.18.1")
    version.write_text("0.18.2\n", encoding="utf-8")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    section = '''## 0.18.2\n\n### Monorepo Lazy Intelligence\n\n- Add an explicit component-targeted Project Intelligence selector for monorepos without introducing a second Intelligence store or prompt-based component guessing.\n- Extend Project Intelligence with optional `components` and `shared_relationships` semantic indexes; `aips intelligence context --component <id>` loads only the system summary, target component topics and declared shared relationship topics.\n- Keep component topics lazy when no component is requested, exclude unrelated application topics, and fail explicitly for unknown components instead of falling back to repository-wide preload.\n- Add executable temporary-monorepo lifecycle evidence and promote Scenario 087 from manual to lifecycle.\n- Raise conformance baseline to 125 total / 7 manual / 19 deterministic / 47 lifecycle / 52 agent_eval / 118 automated / 0 uncovered (94.4% automated).\n- Architecture Diagram Impact: N/A — this extends the existing Project Intelligence context-selection contract only; no runtime topology, Role, Skill, Capability category, Approval Gate or Constitution change.\n\n'''
    marker = "# Changelog\n\n"
    if not text.startswith(marker):
        raise RuntimeError("CHANGELOG marker not found")
    changelog.write_text(text.replace(marker, marker + section, 1), encoding="utf-8")

    conformance = ROOT / "docs/CONFORMANCE.md"
    text = conformance.read_text(encoding="utf-8")
    section = '''\n\n## v0.18.2 Monorepo Lazy Intelligence\n\nPromoted evidence:\n\n~~~text\n087 Monorepo Lazy Intelligence -> Lifecycle\n~~~\n\nScenario 087 now executes a temporary Git monorepo with API, Admin and shared-auth areas. Project Intelligence is semantically enriched with explicit component and shared-relationship indexes. Turn Context with `--component api` resolves the system summary, API topic and shared auth relationship while proving the unrelated Admin topic is not preloaded. Context without an explicit component keeps component topics lazy. An unknown component fails explicitly rather than widening scope.\n\nThis release intentionally does not infer component identity from prompt text or folder-name heuristics and does not create a second Intelligence store.\n\nv0.18.2 baseline:\n\n~~~text\nTotal         125\nManual          7\nDeterministic  19\nLifecycle      47\nAgent Eval     52\nAutomated     118\nUncovered       0\nAutomated     94.4%\n~~~\n\nResidual manual gaps remain 004, 021, 022, 028, 039, 054 and 055.\n\nArchitecture Diagram Impact: N/A. This is an additive Project Intelligence selection contract and lifecycle-evidence change only; runtime topology and governance layers are unchanged.\n'''
    conformance.write_text(text.rstrip() + section + "\n", encoding="utf-8")


def main() -> int:
    update_project_intelligence()
    update_templates()
    promote_scenario()
    update_validator()
    update_release_docs()
    result = subprocess.run([sys.executable, str(ROOT / "tests/validate_repository.py")], cwd=ROOT, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        return result.returncode
    print("v0.18.2 release preparation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
