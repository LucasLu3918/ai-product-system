#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

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
    (project / "harness" / "adapters" / "codex").mkdir(parents=True)
    (project / "harness" / "adapters" / "codex" / "AGENTS.md").write_text("# Adapter fixture\n", encoding="utf-8")
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
        context = ctx.get("context") or {}
        always = context.get("always") or []
        require(always == [str(ROOT / "harness" / "BOOTSTRAP.md"), str(ROOT / "SYSTEM_CORE.md")],
                "fixed AIPS context must use the compact core while preserving bootstrap")
        require(str(ROOT / "SYSTEM.md") not in always, "compatibility router must no longer occupy the fixed context layer")
        routes = context.get("system_protocol_routes") or {}
        require(routes.get("status") == "READY", "Turn Context must resolve canonical protocol routes")
        require(routes.get("system_core", {}).get("bytes", 99999) <= 8192, "Turn Context must report bounded core size")
        from project_intelligence import compact_context_manifest
        compact = compact_context_manifest(ctx)
        compact_routes = (compact.get("context") or {}).get("system_protocol_routes") or {}
        require(compact_routes == routes, "compact Turn Context must preserve additive system route metadata")
        require("prompt" not in json.dumps(compact_routes), "route metadata must not persist or expose prompt text")
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
        require(str((project / "harness" / "adapters" / "codex" / "AGENTS.md").resolve()) not in runtime_native,
                "nested adapter instructions must not apply to root work")

    nested = json_run([
        sys.executable, str(PI), "context", "--project", str(project),
        "--target-path", "harness/adapters/codex/AGENTS.md", "--runtime", "codex",
        "--prompt", "Review this file", "--format", "json",
    ], env)
    require(str((project / "harness" / "adapters" / "codex" / "AGENTS.md").resolve()) in nested["context"]["runtime_native"],
            "nested instructions must apply at their own target path")

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
    require("system_protocol_route=general_read status=READY" in hook.stdout, "hook must expose the selected route")
    require("system_core=" + str(ROOT / "SYSTEM_CORE.md") in hook.stdout, "hook must expose compact system core path")
    require(not (project / ".ai").exists(), "Turn Context hook must not auto-attach normal chat project")
    require(not config_projects.exists(), "Turn Context hook must not create external Intelligence for normal chat")

    plain = base / "plain-directory"
    plain.mkdir()
    plain_context = json_run([
        sys.executable, str(PI), "context", "--project", str(plain),
        "--runtime", "codex", "--prompt", "Review the project", "--format", "json",
    ], env)
    require(plain_context["project"]["mode"] == "EPHEMERAL", "non-Git directory must retain basic context")
    require(plain_context["context"]["layers"]["core"]["derived"] is True,
            "non-Git context must keep its bounded core capsule")

    sys.path.insert(0, str(ROOT / "scripts"))
    from turn_intent import classify_prompt, route_system_protocols
    for prompt, expected in (
        ("不要修改程式碼", False),
        ("請解釋 update 指令", False),
        ("Explain the build system", False),
        ("請修好登入功能", True),
    ):
        require(classify_prompt(prompt)[1] is expected, f"incorrect task intent: {prompt}")
    require(classify_prompt("Explain the build system")[0] == "general", "build must not trigger UI routing")
    require(classify_prompt("不要修改程式碼", "write")[1] is True, "explicit write intent must be honored")

    route_cases = (
        ("Open a PR and merge it", False, "publish"),
        ("Plan end-to-end product delivery", True, "product_delivery"),
        ("Improve UI layout and visual style", True, "visual"),
        ("Review security credentials", False, "security"),
        ("Run conformance tests", True, "testing"),
        ("Change the API schema and data flow", True, "api_data"),
        ("Create the product roadmap plan", True, "planning"),
        ("Update documentation and README", True, "documentation"),
        ("Explain this codebase", False, "general_read"),
        ("Implement an unspecified change", True, "general_mutation"),
    )
    for prompt, mutation, expected_category in route_cases:
        route = route_system_protocols(prompt, mutation, str(ROOT))
        require(route["category"] == expected_category, f"incorrect protocol route for {prompt}: {route}")
        require(route["status"] == "READY", f"canonical route sources missing for {prompt}: {route}")
        require(route["system_core"]["path"] == str(ROOT / "SYSTEM_CORE.md"), "route must point at compact system core")
        require(all(Path(item["path"]).is_file() for item in route["protocols"]), f"route source missing for {prompt}")

    general_mutation = route_system_protocols("Implement an unspecified change", True, str(ROOT))
    require([item["id"] for item in general_mutation["protocols"]] == ["orchestrator", "change_impact", "quality_planning"],
            "general mutation must retain conservative protocol fallback")
    mixed_route = route_system_protocols("Update the security API schema and open a PR", True, str(ROOT))
    require(set(mixed_route["matched_categories"]) == {"publish", "security", "api_data"},
            "mixed tasks must retain every matched task route")
    mixed_ids = {item["id"] for item in mixed_route["protocols"]}
    require({"release_readiness", "secret_handling", "change_impact"}.issubset(mixed_ids),
            "mixed tasks must load all relevant publication, security, and API/data protocols")
    missing_routes = route_system_protocols("Implement an unspecified change", True, str(base / "missing-system"))
    require(missing_routes["status"] == "UNAVAILABLE" and "SYSTEM_CORE.md" in missing_routes["missing"],
            "missing route sources must be explicit and unavailable")
    pi = importlib.import_module("project_intelligence")
    with patch.object(pi, "system_root", return_value=base / "missing-system"):
        missing_context = pi.context_manifest(base / "plain-directory", "codex", "Implement an unspecified change")
    require((missing_context.get("fail_policy") or {}).get("mode") == "closed",
            "unavailable canonical routes must fail closed on mutation")
    require("system_protocol_routes_unavailable" in (missing_context.get("fail_policy") or {}).get("reasons", []),
            "route source failure must have an explicit fail-closed reason")
    core_path = ROOT / "SYSTEM_CORE.md"
    bootstrap_path = ROOT / "harness" / "BOOTSTRAP.md"
    base_system_bytes = len(subprocess.run(
        ["git", "show", "HEAD:SYSTEM.md"], cwd=ROOT, check=True, capture_output=True
    ).stdout)
    current_fixed_bytes = core_path.stat().st_size + bootstrap_path.stat().st_size
    prior_fixed_bytes = base_system_bytes + bootstrap_path.stat().st_size
    require(core_path.stat().st_size <= 8192, "fixed system core exceeds 8192 bytes")
    require(1 - (current_fixed_bytes / prior_fixed_bytes) >= 0.60,
            "fixed system layer must shrink by at least 60% against HEAD SYSTEM.md")


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts"))
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
