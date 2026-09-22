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
HARNESS = ROOT / "scripts" / "harness_resolve.py"
TURN_HOOK = ROOT / "scripts" / "turn_context_hook.py"
CLI = ROOT / "bin" / "aips"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(args: list[str], *, env: dict[str, str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, env=env, input=input_text, capture_output=True, text=True)


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True, text=True)


def json_run(args: list[str], env: dict[str, str]) -> dict:
    result = run(args, env=env)
    require(result.returncode == 0, f"command failed: {args}: {result.stdout} {result.stderr}")
    return json.loads(result.stdout)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    git(path, "init", "-q")
    git(path, "branch", "-m", "main")
    git(path, "config", "user.email", "aips@example.invalid")
    git(path, "config", "user.name", "AIPS Evidence")


def source_registry_runtime_dedup(base: Path, env: dict[str, str]) -> None:
    project = base / "dedup-project"
    init_repo(project)
    (project / "docs").mkdir()
    (project / "AGENTS.md").write_text("# Project rules\nUse project architecture.\n", encoding="utf-8")
    (project / "CLAUDE.md").write_text("# Claude project rules\n", encoding="utf-8")
    (project / "GEMINI.md").write_text("# Gemini project rules\n", encoding="utf-8")
    (project / "docs" / "ARCHITECTURE.md").write_text("# Architecture\nOfficial architecture contract.\n", encoding="utf-8")
    (project / "main.py").write_text("print('ok')\n", encoding="utf-8")
    git(project, "add", "-A")
    git(project, "commit", "-qm", "baseline")

    boot = json_run(
        [sys.executable, str(PI), "bootstrap", "--project", str(project), "--format", "json"],
        env,
    )
    store = Path(boot["store"])
    require(store.is_dir(), "Project Intelligence store missing after bootstrap")
    registry = load_yaml(store / "SOURCE_REGISTRY.yaml")
    require(registry.get("deduplication") == {
        "storage": "pointer_over_copy",
        "runtime_context": "runtime_aware",
    }, "Source Registry deduplication contract missing")

    sources = {str(item.get("path")): item for item in (registry.get("sources") or [])}
    for path in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "docs/ARCHITECTURE.md"):
        require(path in sources, f"Source Registry missing pointer: {path}")
        require(sources[path].get("content_duplicated") is False, f"Source content must remain pointer-only: {path}")

    require(sources["AGENTS.md"].get("auto_loaded_by") == ["codex"], "AGENTS runtime visibility mismatch")
    require(sources["CLAUDE.md"].get("auto_loaded_by") == ["claude-code"], "CLAUDE runtime visibility mismatch")
    require(sources["GEMINI.md"].get("auto_loaded_by") == ["gemini-cli"], "GEMINI runtime visibility mismatch")
    require(sources["docs/ARCHITECTURE.md"].get("auto_loaded_by") == [], "Official doc must not claim native runtime auto-load")

    expected_native = {
        "codex": "AGENTS.md",
        "claude-code": "CLAUDE.md",
        "gemini-cli": "GEMINI.md",
    }
    for runtime, native_name in expected_native.items():
        ctx = json_run(
            [
                sys.executable, str(PI), "context",
                "--project", str(project),
                "--runtime", runtime,
                "--prompt", "Explain the current project architecture.",
                "--format", "json",
            ],
            env,
        )
        runtime_native = [str(Path(p).resolve()) for p in (ctx.get("context") or {}).get("runtime_native", [])]
        project_native = [str(Path(p).resolve()) for p in (ctx.get("context") or {}).get("project_native", [])]
        native_path = str((project / native_name).resolve())
        require(native_path in runtime_native, f"{runtime} must recognize its native instruction pointer")
        require(native_path not in project_native, f"{runtime} native source must not be reinjected as project-native context")
        require(set(runtime_native).isdisjoint(project_native), f"{runtime} context contains duplicated source pointers")
        require(
            str((project / "docs" / "ARCHITECTURE.md").resolve()) in project_native,
            f"{runtime} must retain targeted-load pointer for non-native authoritative docs",
        )

    intel = load_yaml(store / "PROJECT_INTELLIGENCE.yaml")
    require((intel.get("topics") or {}) == {}, "deterministic bootstrap must not copy authoritative source content into derived topics")



def material_instruction_conflict_surface(base: Path, env: dict[str, str]) -> None:
    project = base / "instruction-conflict-project"
    init_repo(project)
    (project / "docs").mkdir()
    (project / "AGENTS.md").write_text("# Project instructions\nArchitecture changes require ADR alignment.\n", encoding="utf-8")
    (project / "docs" / "ADR-001.md").write_text("# ADR 001\nOfficial architecture rule.\n", encoding="utf-8")
    (project / "main.py").write_text("print('ok')\n", encoding="utf-8")
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
    require(str((project / "AGENTS.md").resolve()) in runtime_native, "runtime-native AGENTS source must be preserved")
    require(str((project / "docs" / "ADR-001.md").resolve()) in project_native, "official ADR source must be preserved")
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

def normal_chat_no_bootstrap(base: Path, env: dict[str, str]) -> None:
    project = base / "chat-project"
    init_repo(project)
    (project / "README.md").write_text("# Chat fixture\n", encoding="utf-8")
    git(project, "add", "README.md")
    git(project, "commit", "-qm", "baseline")

    config_projects = Path(env["XDG_CONFIG_HOME"]) / "aips" / "projects"
    require(not (project / ".ai").exists(), "fresh normal-chat fixture unexpectedly attached")
    require(not config_projects.exists(), "fresh normal-chat fixture unexpectedly has external Intelligence")

    ctx = json_run(
        [
            sys.executable, str(PI), "context",
            "--project", str(project),
            "--runtime", "claude-code",
            "--prompt", "What is the difference between a list and a tuple in Python?",
            "--format", "json",
        ],
        env,
    )
    require((ctx.get("task") or {}).get("mutation_likely") is False, "general knowledge prompt must not be classified as mutation")
    require((ctx.get("freshness") or {}).get("status") == "MISSING", "fresh project should report Intelligence MISSING")
    require((ctx.get("requirements") or {}).get("change_impact_required") is False, "normal chat must not require Change Impact")
    require(not (project / ".ai").exists(), "normal context resolution must not create project .ai")
    require(not config_projects.exists(), "normal context resolution must not bootstrap external Intelligence")

    harness = json_run(
        [
            sys.executable, str(HARNESS),
            "--runtime", "claude-code",
            "--project", str(project),
            "--format", "json",
        ],
        env,
    )
    require((harness.get("project") or {}).get("mode") == "EPHEMERAL", "normal chat project must remain EPHEMERAL")
    require((harness.get("intelligence") or {}).get("available") is False, "Harness must report missing Intelligence truthfully")
    require(not config_projects.exists(), "Harness resolution must not bootstrap Intelligence")

    hook_env = dict(env)
    hook_env["AIPS_BIN"] = str(CLI)
    hook_env["CLAUDE_PROJECT_DIR"] = str(project)
    hook = run(
        [sys.executable, str(TURN_HOOK), "--runtime", "claude-code"],
        env=hook_env,
        input_text=json.dumps({"prompt": "Explain Python dictionaries."}),
    )
    require(hook.returncode == 0, f"Turn Context hook failed: {hook.stdout} {hook.stderr}")
    require("AIPS TURN CONTEXT" in hook.stdout, "normal chat may still receive compact Harness context")
    require("mutation_likely=False" in hook.stdout, "normal chat context must remain non-mutating")
    require(not (project / ".ai").exists(), "Turn Context hook must not auto-attach normal chat project")
    require(not config_projects.exists(), "Turn Context hook must not create external Intelligence for normal chat")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        config = base / "config"
        home.mkdir()
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(config)

        source_registry_runtime_dedup(base, env)
        material_instruction_conflict_surface(base, env)
        # Use a separate config root so the dedup fixture's Intelligence cannot affect the normal-chat assertion.
        chat_env = dict(env)
        chat_env["XDG_CONFIG_HOME"] = str(base / "chat-config")
        normal_chat_no_bootstrap(base, chat_env)

    print("intelligence_context_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
