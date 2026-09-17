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


def run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, capture_output=True, text=True)


def json_run(args: list[str], env: dict[str, str]) -> dict:
    result = run(args, env)
    require(result.returncode == 0, f"command failed: {args}: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    git(path, "init", "-q")
    git(path, "branch", "-m", "main")
    git(path, "config", "user.email", "aips@example.invalid")
    git(path, "config", "user.name", "AIPS Evidence")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        project = base / "monorepo"
        home = base / "home"
        config = base / "config"
        home.mkdir()
        init_repo(project)

        for path, body in {
            "apps/api/main.py": "print('api')\n",
            "apps/admin/main.py": "print('admin')\n",
            "packages/shared/auth.py": "AUTH_VERSION = 1\n",
            "README.md": "# Monorepo fixture\n",
        }.items():
            target = project / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
        git(project, "add", "-A")
        git(project, "commit", "-qm", "baseline")

        env = dict(os.environ)
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(config)

        boot = json_run([
            sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json",
        ], env)
        store = Path(boot["store"])
        topics = store / "topics"
        (topics / "components").mkdir(parents=True, exist_ok=True)
        (topics / "shared").mkdir(parents=True, exist_ok=True)
        (topics / "components" / "api.md").write_text("# API component\nOwns public HTTP endpoints.\n", encoding="utf-8")
        (topics / "components" / "admin.md").write_text("# Admin component\nOwns internal admin UI.\n", encoding="utf-8")
        (topics / "shared" / "auth-contract.md").write_text("# Auth contract\nShared authentication relationship.\n", encoding="utf-8")

        intel_path = store / "PROJECT_INTELLIGENCE.yaml"
        intel = load_yaml(intel_path)
        intel["architecture"] = {
            "summary": "Monorepo with API and Admin applications sharing authentication contracts.",
            "confidence": "high",
            "source": "semantic_fixture",
        }
        intel["components"] = {
            "api": {
                "root": "apps/api",
                "topics": ["topics/components/api.md"],
                "shared_relationships": ["auth-contract"],
            },
            "admin": {
                "root": "apps/admin",
                "topics": ["topics/components/admin.md"],
                "shared_relationships": [],
            },
        }
        intel["shared_relationships"] = {
            "auth-contract": {
                "path": "topics/shared/auth-contract.md",
                "components": ["api", "admin"],
            },
        }
        intel_path.write_text(yaml.safe_dump(intel, sort_keys=False), encoding="utf-8")

        api_ctx = json_run([
            sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex",
            "--component", "api", "--prompt", "Explain the API component.", "--format", "json",
        ], env)
        component = api_ctx.get("component_resolution") or {}
        require(component.get("requested") == "api" and component.get("resolved") is True, "API component must resolve")
        require(component.get("system_summary") == intel["architecture"]["summary"], "system summary must be included")
        require((component.get("target") or {}).get("id") == "api", "target component mismatch")
        require(component.get("excluded_components") == ["admin"], "unrelated Admin component must be excluded")
        shared = component.get("shared_relationships") or []
        require(len(shared) == 1 and shared[0].get("id") == "auth-contract", "shared relationship must resolve")

        loaded = set((api_ctx.get("context") or {}).get("intelligence_topics") or [])
        api_topic = str(store / "topics/components/api.md")
        admin_topic = str(store / "topics/components/admin.md")
        auth_topic = str(store / "topics/shared/auth-contract.md")
        require(api_topic in loaded, "target API topic must be loaded")
        require(auth_topic in loaded, "shared relationship topic must be loaded")
        require(admin_topic not in loaded, "unrelated Admin topic must not be preloaded")

        general_ctx = json_run([
            sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex",
            "--prompt", "Explain the repository at a high level.", "--format", "json",
        ], env)
        general_loaded = set((general_ctx.get("context") or {}).get("intelligence_topics") or [])
        require(api_topic not in general_loaded and admin_topic not in general_loaded,
                "component topics must remain lazy without an explicit component target")

        unknown = run([
            sys.executable, str(PI), "context", "--project", str(project), "--runtime", "codex",
            "--component", "missing", "--prompt", "Explain missing component.", "--format", "json",
        ], env)
        require(unknown.returncode != 0, "unknown component must fail explicitly")
        require("Unknown Project Intelligence component" in unknown.stderr, "unknown component error must be explicit")

    print("monorepo_lazy_intelligence_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
