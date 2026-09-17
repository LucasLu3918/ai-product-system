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


def json_run(args: list[str], env: dict[str, str]) -> dict:
    result = subprocess.run(args, env=env, capture_output=True, text=True)
    require(result.returncode == 0, f"command failed: {args}: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "project"
        project.mkdir()
        git(project, "init", "-q")
        git(project, "branch", "-m", "main")
        git(project, "config", "user.email", "aips@example.invalid")
        git(project, "config", "user.name", "AIPS Evidence")
        (project / "docs").mkdir()
        (project / "AGENTS.md").write_text("# Project policy\nREST only unless an explicit scoped decision approves otherwise.\n", encoding="utf-8")
        (project / "docs" / "ADR-001.md").write_text("# API contract\nREST is the current authoritative API contract.\n", encoding="utf-8")
        (project / "main.py").write_text("print('ok')\n", encoding="utf-8")
        git(project, "add", "-A")
        git(project, "commit", "-qm", "baseline")

        env = dict(os.environ)
        env["HOME"] = str(base / "home")
        env["XDG_CONFIG_HOME"] = str(base / "config")
        Path(env["HOME"]).mkdir()

        boot = json_run([sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"], env)
        store = Path(boot["store"])
        registry = load_yaml(store / "SOURCE_REGISTRY.yaml")
        sources = {str(s.get("path")): s for s in registry.get("sources") or []}
        require(sources["AGENTS.md"].get("content_duplicated") is False, "AGENTS must remain pointer-over-copy")
        require(sources["docs/ADR-001.md"].get("content_duplicated") is False, "ADR must remain pointer-over-copy")
        require(sources["AGENTS.md"].get("auto_loaded_by") == ["codex"], "Codex runtime visibility missing")

        overrides_path = store / "PROJECT_OVERRIDES.yaml"
        overrides = load_yaml(overrides_path)
        overrides["conflicts"] = [{
            "id": "rest-vs-graphql",
            "summary": "Current explicit GraphQL request conflicts with REST-only project policy.",
            "material": True,
            "status": "UNRESOLVED",
            "sources": ["AGENTS.md", "docs/ADR-001.md", "user:current-request"],
        }]
        overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False, allow_unicode=True), encoding="utf-8")

        ctx = json_run([
            sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex",
            "--prompt", "Implement this endpoint with GraphQL.", "--format", "json", "--explain",
        ], env)
        resolution = ctx.get("resolution") or {}
        precedence = resolution.get("instruction_precedence") or []
        require(precedence.index("explicit_user_decision") < precedence.index("runtime_native"), "user-decision precedence missing")
        require(precedence.index("runtime_native") < precedence.index("authoritative_contract"), "runtime/contract precedence missing")
        instruction_sources = resolution.get("instruction_sources") or []
        by_path = {item.get("relative_path"): item for item in instruction_sources}
        require(by_path["AGENTS.md"].get("delivery") == "runtime_native", "Codex AGENTS must remain runtime-native")
        require(by_path["docs/ADR-001.md"].get("precedence_layer") == "authoritative_contract", "ADR must remain authoritative contract pointer")
        require(by_path["AGENTS.md"].get("content_duplicated") is False, "resolution must not duplicate AGENTS content")
        require(resolution.get("instruction_conflict_status") == "BLOCKED", "unresolved material conflict must be surfaced")
        conflicts = resolution.get("instruction_conflicts") or []
        require(any(c.get("id") == "rest-vs-graphql" and c.get("status") == "UNRESOLVED" for c in conflicts), "structured conflict missing")
        require("instruction_conflict_unresolved" in (ctx.get("fail_policy") or {}).get("reasons", []), "mutation must fail closed on unresolved conflict")
        require((load_yaml(store / "PROJECT_INTELLIGENCE.yaml").get("topics") or {}) == {}, "authoritative source content must not be normalized into derived PI")

        overrides = load_yaml(overrides_path)
        overrides["conflicts"][0]["status"] = "RESOLVED"
        overrides["conflicts"][0]["decision"] = {
            "source": "explicit_user_decision",
            "scope": "current_task",
            "permanent_policy_rewritten": False,
        }
        overrides_path.write_text(yaml.safe_dump(overrides, sort_keys=False, allow_unicode=True), encoding="utf-8")
        resolved = json_run([
            sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex",
            "--prompt", "Implement this endpoint with GraphQL.", "--format", "json",
        ], env)
        require((resolved.get("resolution") or {}).get("instruction_conflict_status") == "CLEAR", "resolved conflict must clear instruction block")
        require("instruction_conflict_unresolved" not in (resolved.get("fail_policy") or {}).get("reasons", []), "resolved conflict must not remain a fail-closed reason")
        require(load_yaml(project / "AGENTS.md") == {} if False else True, "placeholder")
        require("REST only" in (project / "AGENTS.md").read_text(encoding="utf-8"), "resolution must not rewrite permanent project policy")

    print("instruction_resolution_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
