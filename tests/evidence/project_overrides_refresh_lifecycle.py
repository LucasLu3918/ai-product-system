#!/usr/bin/env python3
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
