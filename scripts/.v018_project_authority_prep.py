#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PI = ROOT / "scripts" / "project_intelligence.py"
DOC = ROOT / "orchestration" / "PROJECT_INTELLIGENCE.md"
EVIDENCE = ROOT / "tests" / "evidence" / "project_override_reconciliation_lifecycle.py"


def patch_pi() -> None:
    text = PI.read_text(encoding="utf-8")

    anchor = '''def context_manifest(root: Path, runtime: str, prompt: str, explain: bool = False) -> dict[str, Any]:\n'''
    block = '''def _canonical_value(value: Any) -> str:\n    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))\n\n\ndef active_authority_conflicts(store: Path, intel: dict[str, Any] | None = None) -> list[dict[str, Any]]:\n    intel = intel or {}\n    overrides = load_yaml(store / "PROJECT_OVERRIDES.yaml", {"conflicts": []})\n    result: list[dict[str, Any]] = []\n    for origin, items in (("project_overrides", overrides.get("conflicts") or []), ("project_intelligence", intel.get("conflicts") or [])):\n        for item in items:\n            if not isinstance(item, dict):\n                continue\n            if str(item.get("status", "OPEN")).upper() in {"RESOLVED", "DISMISSED"}:\n                continue\n            entry = dict(item)\n            entry.setdefault("origin", origin)\n            result.append(entry)\n    return result\n\n\ndef reconcile_overrides(root: Path) -> dict[str, Any]:\n    store, mode, pid = intelligence_store(root)\n    intel_path = store / "PROJECT_INTELLIGENCE.yaml"\n    overrides_path = store / "PROJECT_OVERRIDES.yaml"\n    discovery_path = store / "DISCOVERY.yaml"\n    if not intel_path.exists() or not overrides_path.exists() or not discovery_path.exists():\n        raise RuntimeError("Project Intelligence, PROJECT_OVERRIDES and DISCOVERY must exist before reconciliation")\n\n    with writer_lock(store):\n        overrides = load_yaml(overrides_path, {})\n        discovery = load_yaml(discovery_path, {})\n        discovered: dict[str, dict[str, Any]] = {}\n        for item in discovery.get("inferences") or []:\n            if not isinstance(item, dict) or not item.get("id") or "value" not in item:\n                continue\n            discovered[str(item["id"])] = item\n\n        generated: list[dict[str, Any]] = []\n        preserved_assertions = 0\n        categories = ("approved_inferences", "additional_rules", "exceptions", "excluded_inferences")\n        for category in categories:\n            for assertion in overrides.get(category) or []:\n                if not isinstance(assertion, dict) or not assertion.get("id") or "value" not in assertion:\n                    continue\n                preserved_assertions += 1\n                assertion_id = str(assertion["id"])
                candidate = discovered.get(assertion_id)\n                if not candidate or _canonical_value(candidate.get("value")) == _canonical_value(assertion.get("value")):\n                    continue\n                conflict_seed = _canonical_value({\n                    "category": category,\n                    "assertion_id": assertion_id,\n                    "approved_value": assertion.get("value"),\n                    "discovered_value": candidate.get("value"),\n                })\n                generated.append({\n                    "id": f"conflict-{sha(conflict_seed)[:12]}",\n                    "type": "override_discovery_contradiction",\n                    "status": "OPEN",\n                    "override_category": category,\n                    "assertion_id": assertion_id,\n                    "approved_value": assertion.get("value"),\n                    "discovered_value": candidate.get("value"),\n                    "evidence": candidate.get("evidence") or [],\n                    "source": "deterministic_override_reconciliation",\n                })\n\n        existing = [item for item in (overrides.get("conflicts") or []) if isinstance(item, dict)]\n        existing_ids = {str(item.get("id")) for item in existing if item.get("id")}\n        for conflict in generated:\n            if conflict["id"] not in existing_ids:\n                existing.append(conflict)\n                existing_ids.add(conflict["id"])\n        overrides["conflicts"] = existing\n        atomic_yaml(overrides_path, overrides)\n\n    active = [item for item in existing if str(item.get("status", "OPEN")).upper() not in {"RESOLVED", "DISMISSED"}]\n    return {\n        "project_id": pid,\n        "mode": mode,\n        "preserved_assertions": preserved_assertions,\n        "discovered_inferences": len(discovered),\n        "new_conflicts": len([item for item in generated if item["id"] in existing_ids]),\n        "active_conflicts": len(active),\n        "conflicts": active,\n    }\n\n\n'''
    if "def reconcile_overrides(root: Path)" not in text:
        if anchor not in text:
            raise RuntimeError("context_manifest anchor not found")
        text = text.replace(anchor, block + anchor, 1)

    old = '''    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []}) if store.exists() else {"sources": []}\n    state = intel.get("state") or {}\n'''
    new = '''    registry = load_yaml(store / "SOURCE_REGISTRY.yaml", {"sources": []}) if store.exists() else {"sources": []}\n    state = intel.get("state") or {}\n    authority_conflicts = active_authority_conflicts(store, intel) if store.exists() else []\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif "authority_conflicts = active_authority_conflicts" not in text:
        raise RuntimeError("context registry/state anchor not found")

    old = '''        if readiness != "READY":\n            fail_closed_reasons.append(f"intelligence_readiness_{readiness.lower()}")\n\n    return {\n'''
    new = '''        if readiness != "READY":\n            fail_closed_reasons.append(f"intelligence_readiness_{readiness.lower()}")\n        if authority_conflicts:\n            fail_closed_reasons.append("unresolved_authority_conflict")\n\n    return {\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif 'fail_closed_reasons.append("unresolved_authority_conflict")' not in text:
        raise RuntimeError("fail policy anchor not found")

    old = '''            "optional_evidence": [str(store / "DISCOVERY.yaml")] if (store / "DISCOVERY.yaml").exists() else [],\n        },\n        "intelligence": {\n'''
    new = '''            "optional_evidence": [str(store / "DISCOVERY.yaml")] if (store / "DISCOVERY.yaml").exists() else [],\n            "authority_conflicts": authority_conflicts,\n        },\n        "intelligence": {\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif '"authority_conflicts": authority_conflicts' not in text:
        raise RuntimeError("context output anchor not found")

    old = '''    for name in ("bootstrap", "status", "render", "finalize", "migrate-attached", "sync-external"):\n'''
    new = '''    for name in ("bootstrap", "status", "render", "finalize", "migrate-attached", "sync-external", "reconcile-overrides"):\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif '"reconcile-overrides"' not in text:
        raise RuntimeError("CLI parser anchor not found")

    old = '''        elif args.command == "sync-external":\n            result = sync_external(root)\n        else:\n'''
    new = '''        elif args.command == "sync-external":\n            result = sync_external(root)\n        elif args.command == "reconcile-overrides":\n            result = reconcile_overrides(root)\n        else:\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif 'args.command == "reconcile-overrides"' not in text:
        raise RuntimeError("CLI dispatch anchor not found")

    PI.write_text(text, encoding="utf-8")


def write_evidence() -> None:
    EVIDENCE.write_text(r'''#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
PI = ROOT / "scripts" / "project_intelligence.py"


def run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, capture_output=True, text=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        home = base / "home"
        config = base / "config"
        project.mkdir()
        home.mkdir()
        (project / "AGENTS.md").write_text("# Rules\nPreserve domain boundaries.\n", encoding="utf-8")
        (project / "main.py").write_text("print('fixture')\n", encoding="utf-8")
        git(project, "init", "-q")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Test")
        git(project, "add", "AGENTS.md", "main.py")
        git(project, "commit", "-qm", "initial")

        env = dict(os.environ)
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(config)

        first = run([sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"], env)
        require(first.returncode == 0, f"initial bootstrap failed: {first.stdout} {first.stderr}")
        store = Path(json.loads(first.stdout)["store"])
        overrides_path = store / "PROJECT_OVERRIDES.yaml"
        overrides = load_yaml(overrides_path)
        approved = {
            "id": "architecture.domain_boundary",
            "value": "isolated-domain",
            "approved_by": "project-owner",
            "evidence": ["AGENTS.md"],
        }
        overrides["approved_inferences"] = [approved]
        overrides["additional_rules"] = [{"id": "testing.minimum", "value": "characterization-first"}]
        overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False), encoding="utf-8")

        (project / "docs").mkdir()
        (project / "docs" / "architecture.md").write_text("New scan evidence for fixture.\n", encoding="utf-8")
        git(project, "add", "docs/architecture.md")
        git(project, "commit", "-qm", "new discovery evidence")

        second = run([sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"], env)
        require(second.returncode == 0, f"refresh bootstrap failed: {second.stdout} {second.stderr}")
        after_refresh = load_yaml(overrides_path)
        require(after_refresh.get("approved_inferences") == [approved], "refresh must preserve approved inference")
        require((after_refresh.get("additional_rules") or [])[0].get("value") == "characterization-first", "refresh must preserve additional rule")

        discovery_path = store / "DISCOVERY.yaml"
        discovery = load_yaml(discovery_path)
        discovery["inferences"] = [{
            "id": "architecture.domain_boundary",
            "value": "shared-domain",
            "type": "INTERPRETATION",
            "confidence": "high",
            "evidence": ["docs/architecture.md"],
        }]
        discovery_path.write_text(yaml.safe_dump(discovery, sort_keys=False), encoding="utf-8")

        reconcile = run([sys.executable, str(PI), "reconcile-overrides", "--project", str(project), "--format", "json"], env)
        require(reconcile.returncode == 0, f"reconcile failed: {reconcile.stdout} {reconcile.stderr}")
        result = json.loads(reconcile.stdout)
        require(result.get("active_conflicts") == 1, "contradictory discovery must create one active conflict")

        reconciled = load_yaml(overrides_path)
        require(reconciled.get("approved_inferences") == [approved], "reconciliation must not overwrite approved inference")
        conflicts = reconciled.get("conflicts") or []
        require(len(conflicts) == 1, "conflict must persist in PROJECT_OVERRIDES")
        conflict = conflicts[0]
        require(conflict.get("type") == "override_discovery_contradiction", "wrong conflict type")
        require(conflict.get("approved_value") == "isolated-domain", "approved value must remain visible")
        require(conflict.get("discovered_value") == "shared-domain", "discovered contradiction must remain visible")
        require(conflict.get("evidence") == ["docs/architecture.md"], "conflict evidence must be retained")

        again = run([sys.executable, str(PI), "reconcile-overrides", "--project", str(project), "--format", "json"], env)
        require(again.returncode == 0, "idempotent reconciliation failed")
        require(len(load_yaml(overrides_path).get("conflicts") or []) == 1, "reconciliation must not duplicate same conflict")

        context = run([
            sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex",
            "--prompt", "modify API handler", "--format", "json", "--explain",
        ], env)
        require(context.returncode == 0, f"context failed: {context.stdout} {context.stderr}")
        context_doc = json.loads(context.stdout)
        surfaced = (context_doc.get("context") or {}).get("authority_conflicts") or []
        require(len(surfaced) == 1, "active authority conflict must surface in turn context")
        fail_reasons = (context_doc.get("fail_policy") or {}).get("reasons") or []
        require("unresolved_authority_conflict" in fail_reasons, "mutation must fail closed on unresolved authority conflict")

    print("project_override_reconciliation_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''', encoding="utf-8")


def update_doc() -> None:
    text = DOC.read_text(encoding="utf-8")
    marker = '''User corrections persist in `PROJECT_OVERRIDES.yaml`, not by editing generated HTML.\n'''
    addition = '''User corrections persist in `PROJECT_OVERRIDES.yaml`, not by editing generated HTML.\n\n### Override reconciliation\n\nLater semantic discovery may emit structured `DISCOVERY.yaml` inferences with an `id`, `value`, and evidence. Run `aips intelligence reconcile-overrides` after such enrichment. The deterministic reconciler compares matching structured assertions in `approved_inferences`, `additional_rules`, `exceptions`, and `excluded_inferences`. It never replaces an approved override. A contradictory value is appended as an idempotent `OPEN` conflict in `PROJECT_OVERRIDES.yaml`.\n\nActive authority conflicts are included in the Turn Context Manifest. Material mutation fails closed with `unresolved_authority_conflict` until a human resolves or dismisses the conflict. This mechanism surfaces registered semantic contradictions; it does not guess conflicts by keyword-matching arbitrary Markdown.\n'''
    if "### Override reconciliation" not in text:
        if marker not in text:
            raise RuntimeError("Project Intelligence override marker not found")
        text = text.replace(marker, addition, 1)
    DOC.write_text(text, encoding="utf-8")


def main() -> int:
    patch_pi()
    write_evidence()
    update_doc()
    subprocess.run([sys.executable, "-m", "py_compile", str(PI), str(EVIDENCE)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(EVIDENCE)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tests" / "validate_repository.py")], cwd=ROOT, check=True)
    print("v0.18.0 project authority capability prep: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
