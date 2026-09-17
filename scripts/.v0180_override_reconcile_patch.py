#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PI = ROOT / "scripts" / "project_intelligence.py"
DOC = ROOT / "orchestration" / "PROJECT_INTELLIGENCE.md"
TEST = ROOT / "tests" / "evidence" / "project_overrides_refresh_lifecycle.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected marker exactly once, found {text.count(old)}")
    return text.replace(old, new, 1)


def patch_pi() -> None:
    text = PI.read_text(encoding="utf-8")
    marker = '''def topic_is_complete(store: Path, name: str, topic: Any) -> bool:\n'''
    helpers = '''def canonical_semantic_value(value: Any) -> str:\n    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))\n\n\ndef reconcile_overrides(root: Path, observations_file: Path) -> dict[str, Any]:\n    store, mode, pid = intelligence_store(root)\n    overrides_path = store / "PROJECT_OVERRIDES.yaml"\n    if not overrides_path.exists():\n        raise RuntimeError("Project Intelligence is not initialized")\n    if not observations_file.is_file():\n        raise RuntimeError(f"Discovery observations file not found: {observations_file}")\n    observations_doc = load_yaml(observations_file, {})\n    observations = observations_doc.get("observations") or []\n    if not isinstance(observations, list):\n        raise RuntimeError("Discovery observations must be a list")\n\n    with writer_lock(store):\n        overrides = load_yaml(overrides_path, {})\n        protected_sections = ("approved_inferences", "additional_rules", "exceptions", "excluded_inferences")\n        before = {name: canonical_semantic_value(overrides.get(name) or []) for name in protected_sections}\n        existing_conflicts = list(overrides.get("conflicts") or [])\n        by_id = {str(item.get("id")): item for item in existing_conflicts if isinstance(item, dict) and item.get("id")}\n        added: list[str] = []\n\n        candidates: list[tuple[str, dict[str, Any]]] = []\n        for section in protected_sections:\n            for raw in overrides.get(section) or []:\n                if isinstance(raw, dict) and raw.get("key") is not None:\n                    candidates.append((section, raw))\n\n        for observation in observations:\n            if not isinstance(observation, dict) or observation.get("key") is None:\n                continue\n            key = str(observation["key"])\n            observed_value = observation.get("value")\n            for section, approved in candidates:\n                if str(approved.get("key")) != key:\n                    continue\n                if section == "excluded_inferences":\n                    contradictory = approved.get("value") is None or canonical_semantic_value(approved.get("value")) == canonical_semantic_value(observed_value)\n                else:\n                    contradictory = canonical_semantic_value(approved.get("value")) != canonical_semantic_value(observed_value)\n                if not contradictory:\n                    continue\n                conflict_id = "override-discovery-" + sha(\n                    section + ":" + key + ":" + canonical_semantic_value(approved.get("value")) + ":" + canonical_semantic_value(observed_value)\n                )[:16]\n                if conflict_id in by_id:\n                    continue\n                conflict = {\n                    "id": conflict_id,\n                    "type": "override_discovery_conflict",\n                    "summary": f"Discovery for {key} conflicts with user-approved {section}.",\n                    "material": True,\n                    "status": "UNRESOLVED",\n                    "key": key,\n                    "override_section": section,\n                    "approved_value": approved.get("value"),\n                    "discovered_value": observed_value,\n                    "sources": list(observation.get("evidence") or []),\n                }\n                existing_conflicts.append(conflict)\n                by_id[conflict_id] = conflict\n                added.append(conflict_id)\n\n        for name in protected_sections:\n            if canonical_semantic_value(overrides.get(name) or []) != before[name]:\n                raise RuntimeError(f"Protected override section changed during reconciliation: {name}")\n        overrides["conflicts"] = existing_conflicts\n        atomic_yaml(overrides_path, overrides)\n\n    review = render_review(root)\n    return {\n        "project_id": pid,\n        "mode": mode,\n        "status": "CONFLICT" if added else "UNCHANGED",\n        "added_conflicts": added,\n        "conflict_count": len(existing_conflicts),\n        "overrides_preserved": True,\n        "review_html": str(review),\n    }\n\n\n''' + marker
    text = replace_once(text, marker, helpers, "override reconciliation helpers")

    marker = '''    p = sub.add_parser("impact-init")\n'''
    addition = '''    p = sub.add_parser("reconcile-overrides")\n    p.add_argument("--project", default=os.getcwd())\n    p.add_argument("--observations-file", required=True)\n    p.add_argument("--format", choices=["yaml", "json"], default="yaml")\n\n''' + marker
    text = replace_once(text, marker, addition, "reconcile parser")

    old = '''        elif args.command == "impact-init":\n            result = impact_init(root, args.prompt, args.change_id)\n'''
    new = '''        elif args.command == "reconcile-overrides":\n            result = reconcile_overrides(root, Path(args.observations_file).resolve())\n        elif args.command == "impact-init":\n            result = impact_init(root, args.prompt, args.change_id)\n'''
    text = replace_once(text, old, new, "reconcile dispatch")
    PI.write_text(text, encoding="utf-8")


def patch_doc() -> None:
    text = DOC.read_text(encoding="utf-8")
    marker = '''If new evidence conflicts with an override, mark a conflict for human review.\n'''
    addition = marker + '''\nSemantic discovery remains an Agent responsibility. When refreshed discovery produces structured observations (`key`, `value`, `evidence`), run `aips intelligence reconcile-overrides --project <path> --observations-file <yaml>` before accepting refreshed conclusions. The deterministic reconciler compares those observations with structured user-approved entries in `PROJECT_OVERRIDES.yaml`, preserves `approved_inferences`, `additional_rules`, `exceptions`, and `excluded_inferences` byte-semantically, and appends an idempotent unresolved conflict instead of replacing an approved decision.\n'''
    text = replace_once(text, marker, addition, "override reconciliation docs")
    DOC.write_text(text, encoding="utf-8")


def write_test() -> None:
    TEST.write_text(r'''#!/usr/bin/env python3
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def run_json(args: list[str], env: dict[str, str]) -> dict:
    result = subprocess.run(args, env=env, capture_output=True, text=True)
    require(result.returncode == 0, f"command failed: {args}: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        project.mkdir()
        git(project, "init", "-q")
        git(project, "branch", "-m", "main")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Evidence")
        (project / "main.py").write_text("print('ok')\n", encoding="utf-8")
        git(project, "add", "main.py")
        git(project, "commit", "-qm", "baseline")

        env = dict(os.environ)
        env["HOME"] = str(base / "home")
        env["XDG_CONFIG_HOME"] = str(base / "config")
        Path(env["HOME"]).mkdir()

        boot = run_json([sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"], env)
        store = Path(boot["store"])
        overrides_path = store / "PROJECT_OVERRIDES.yaml"
        overrides = load_yaml(overrides_path)
        overrides["approved_inferences"] = [{"key": "architecture.style", "value": "clean", "approved_by": "user"}]
        overrides["additional_rules"] = [{"key": "testing.minimum", "value": "integration", "approved_by": "user"}]
        overrides["exceptions"] = [{"key": "legacy.auth", "value": "temporary_exception", "approved_by": "user"}]
        overrides["excluded_inferences"] = [{"key": "database.orm", "value": "active_record", "approved_by": "user"}]
        overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False, allow_unicode=True), encoding="utf-8")
        before = load_yaml(overrides_path)
        protected = {name: canonical(before.get(name) or []) for name in ("approved_inferences", "additional_rules", "exceptions", "excluded_inferences")}

        observations = base / "observations.yaml"
        observations.write_text(yaml.safe_dump({"observations": [
            {"key": "architecture.style", "value": "layered", "evidence": ["src/app.py", "src/domain.py"]},
            {"key": "testing.minimum", "value": "integration", "evidence": ["tests/integration"]},
            {"key": "database.orm", "value": "active_record", "evidence": ["requirements.txt"]},
            {"key": "unrelated.fact", "value": True, "evidence": ["README.md"]},
        ]}, sort_keys=False), encoding="utf-8")

        first = run_json([
            sys.executable, str(PI), "reconcile-overrides", "--project", str(project),
            "--observations-file", str(observations), "--format", "json",
        ], env)
        require(first.get("status") == "CONFLICT", "contradictory discovery must report CONFLICT")
        require(first.get("overrides_preserved") is True, "reconciliation must report override preservation")
        after = load_yaml(overrides_path)
        for name, snapshot in protected.items():
            require(canonical(after.get(name) or []) == snapshot, f"{name} was overwritten by discovery")
        conflicts = after.get("conflicts") or []
        require(any(c.get("key") == "architecture.style" and c.get("status") == "UNRESOLVED" for c in conflicts), "approved inference contradiction must become conflict")
        require(any(c.get("key") == "database.orm" and c.get("override_section") == "excluded_inferences" for c in conflicts), "excluded inference reappearance must become conflict")
        require(not any(c.get("key") == "testing.minimum" for c in conflicts), "matching discovery must not create conflict")
        first_count = len(conflicts)

        second = run_json([
            sys.executable, str(PI), "reconcile-overrides", "--project", str(project),
            "--observations-file", str(observations), "--format", "json",
        ], env)
        require(second.get("status") == "UNCHANGED", "repeat reconciliation must be idempotent")
        require(len(load_yaml(overrides_path).get("conflicts") or []) == first_count, "repeat reconciliation duplicated conflicts")

        ctx = run_json([
            sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex",
            "--prompt", "Implement a small refactor.", "--format", "json",
        ], env)
        require((ctx.get("resolution") or {}).get("instruction_conflict_status") == "BLOCKED", "override/discovery conflict must surface through Turn Context")
        require("instruction_conflict_unresolved" in (ctx.get("fail_policy") or {}).get("reasons", []), "mutation must fail closed on unresolved override conflict")

    print("project_overrides_refresh_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''', encoding="utf-8")


def main() -> int:
    patch_pi()
    patch_doc()
    write_test()
    print("v0.18.0 override reconciliation capability patch: APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
