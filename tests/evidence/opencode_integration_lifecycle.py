"""Credential-free OpenCode projection and Harness lifecycle evidence."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import creative_workspace_profile as creative_profile
import opencode_native_guard as native_guard
import opencode_skill_projection as projection
import opencode_trace
import turn_intent


def run(args, env, *, ok=True):
    result = subprocess.run(args, env=env, cwd=ROOT, text=True, capture_output=True, timeout=60, check=False)
    if ok:
        assert result.returncode == 0, (args, result.stdout, result.stderr)
    return result


def expect_blocked(action):
    try:
        action()
    except (ValueError, OSError):
        return
    raise AssertionError("unsafe action accepted")


def ownership_cases(base):
    manager = projection.OwnedFiles("skills", base / "native", base / "owned")
    rel = "skills/tdd/SKILL.md"
    assert manager.sync({rel: "first"})["status"] == "READY"
    assert manager.sync({rel: "first"})["status"] == "READY"
    assert manager.sync({rel: "next"})["status"] == "READY"
    target = manager.target(rel)
    target.write_text("user edit")
    before = manager.manifest.read_bytes()
    assert manager.sync({rel: "third"})["status"] == "CONFLICT"
    assert manager.manifest.read_bytes() == before, "conflict dropped ownership"
    assert manager.sync({})["status"] == "CONFLICT"
    assert target.read_text() == "user edit"
    target.write_text("next")
    assert manager.sync({})["status"] == "READY"
    assert not target.exists()
    target.write_text("user skill")
    assert manager.sync({rel: "aips"})["status"] == "CONFLICT"
    assert target.read_text() == "user skill"
    target.unlink()
    manager.sync({rel: "recorded"})
    assert manager.status({rel: "new canonical"})["status"] == "DRIFT"
    manifest = manager.manifest.read_bytes()
    manager.manifest.write_text("{broken")
    expect_blocked(lambda: manager.sync({}))
    assert target.read_text() == "recorded"
    manager.manifest.write_bytes(manifest)
    data = json.loads(manifest)
    data["files"]["../../escape"] = "a" * 64
    manager.manifest.write_text(json.dumps(data))
    expect_blocked(lambda: manager.sync({}))
    manager.manifest.write_bytes(manifest)
    data = json.loads(manifest)
    data["root"] = str(base / "other")
    manager.manifest.write_text(json.dumps(data))
    expect_blocked(lambda: manager.sync({}))
    manager.manifest.write_bytes(manifest)
    target.unlink()
    outside = base / "outside"
    outside.write_text("untouched")
    target.symlink_to(outside)
    expect_blocked(lambda: manager.sync({rel: "overwrite"}))
    expect_blocked(lambda: manager.sync({}))
    assert outside.read_text() == "untouched"
    target.unlink()
    target.parent.rmdir()
    target.parent.symlink_to(base)
    expect_blocked(lambda: manager.sync({rel: "escape"}))
    target.parent.unlink()
    expect_blocked(lambda: manager.sync({"skills/../escape": "bad"}))
    # Interrupted checkpoint leaves the old manifest intact and refuses adoption.
    manager.sync({rel: "recorded"})
    original = projection.atomic_write
    def interrupted(path, body):
        if path == manager.manifest:
            raise OSError("simulated interrupted manifest write")
        return original(path, body)
    with patch.object(projection, "atomic_write", interrupted):
        expect_blocked(lambda: manager.sync({rel: "interrupted"}))
    assert manager.sync({rel: "retry"})["status"] == "CONFLICT"
    assert target.read_text() == "interrupted"
    assert manager.manifest.read_bytes() == manifest


def instruction_cases(base):
    manager = projection.OwnedFiles("instructions", base / "native", base / "owned")
    target = manager.root / "AGENTS.md"
    target.parent.mkdir(parents=True)
    target.write_text("User rules\n")
    body = projection.BEGIN + "\nmanaged\n" + projection.END
    manager.sync({"AGENTS.md": body})
    target.write_text(target.read_text() + "User appended rule\n")
    assert manager.sync({"AGENTS.md": body})["status"] == "READY"
    manager.sync({})
    assert target.read_text() == "User rules\n\nUser appended rule\n"
    target.write_text(body)
    assert manager.sync({"AGENTS.md": body})["status"] == "CONFLICT", "unowned block adopted"
    target.write_text(body + body)
    expect_blocked(lambda: manager.sync({"AGENTS.md": body}))


def cli_cases(base):
    home = base / "home"
    config = base / "config"
    binary = base / "bin"
    home.mkdir(parents=True); binary.mkdir()
    env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(config), AIPS_VALIDATION_PYTHON=sys.executable, PATH=str(binary) + os.pathsep + "/usr/bin:/bin", OPENCODE_CONFIG_DIR=str(config / "opencode"))
    env.pop("CODEX_HOME", None)
    cli = ["bash", str(ROOT / "bin/aips")]
    run(cli + ["harness", "install"], env)
    state = config / "aips/harness/adapters/opencode.yaml"
    assert yaml.safe_load(state.read_text())["status"] == "NOT_DETECTED"
    fake = binary / "opencode"
    fake.write_text("#!/bin/sh\nprintf 'opencode v2.0.24\\n'\n"); fake.chmod(0o755)
    root = config / "opencode"
    root.mkdir(); (root / "opencode.jsonc").write_text('// user comments\n{"model":"user/model"}\n')
    run(cli + ["harness", "install"], env)
    initial = yaml.safe_load(state.read_text())
    assert initial["status"] == "AUTOMATIC"
    assert initial["governance_enforcement"] == "ADVISORY"
    native = list(root.glob("skills/*/SKILL.md"))
    assert len(native) == 27
    for path in native:
        meta = yaml.safe_load(path.read_text().split("---", 2)[1])
        assert meta["name"] == path.parent.name and meta["description"]
    assert len(list(root.glob("commands/aips-*.md"))) == 3
    plugin = root / "plugins/aips-opencode.ts"
    assert plugin.is_file() and str(ROOT.resolve()) in plugin.read_text()
    assert "$ARGUMENTS" in (root / "commands/aips-plan.md").read_text()
    jsonc = (root / "opencode.jsonc").read_bytes()
    before = {p: p.read_bytes() for p in native}
    run(cli + ["harness", "install"], env)
    assert all(path.read_bytes() == text for path, text in before.items())
    run(cli + ["harness", "doctor"], env)
    resolved = json.loads(run(cli + ["harness", "resolve", "--runtime", "opencode", "--project", str(ROOT), "--format", "json"], env).stdout)
    assert str(root / "AGENTS.md") in resolved["runtime"]["native_instructions"]
    configured = json.loads(run(cli + ["mcp", "config", "--client", "opencode"], env).stdout)
    assert configured["automatic_change"] is False
    assert configured["config"]["mcp"]["servers"]["aips"]["environment"]["AIPS_MCP_WORKSPACE"] == str(ROOT)
    assert (root / "opencode.jsonc").read_bytes() == jsonc
    command = root / "commands/aips-plan.md"
    command_body = command.read_text()
    command.write_text(command_body + "user command edit\n")
    assert run(cli + ["harness", "doctor"], env, ok=False).returncode != 0
    command.write_text(command_body)
    v1 = json.loads(run(cli + ["mcp", "config", "--client", "opencode", "--opencode-version", "1"], env).stdout)
    assert v1["config"]["mcp"]["aips"]["enabled"] is True
    changed = root / "skills/tdd/SKILL.md"
    original = changed.read_text(); changed.write_text(original + "user edit\n")
    assert run(cli + ["harness", "doctor"], env, ok=False).returncode != 0
    assert run(cli + ["harness", "uninstall"], env, ok=False).returncode != 0
    assert "user edit" in changed.read_text()
    assert (config / "aips/harness").exists()
    changed.write_text(original)
    run(cli + ["harness", "uninstall"], env)
    assert not list(root.glob("skills/*/SKILL.md"))
    assert not plugin.exists()
    fake.write_text("#!/bin/sh\nprintf 'opencode v1.18.29\\n'\n"); fake.chmod(0o755)
    run(cli + ["harness", "install"], env)
    assert not plugin.exists(), "V2 plugin must not be projected into a V1 runtime"
    run(cli + ["harness", "uninstall"], env)
    fake.write_text("#!/bin/sh\nprintf '99.0.0\\n'\n")
    run(cli + ["harness", "install"], env)
    assert yaml.safe_load(state.read_text())["status"] == "CONFLICT"
    assert not list(root.glob("skills/*/SKILL.md")), "unknown version installed projections"
    fake.write_text("#!/bin/sh\nexit 1\n")
    run(cli + ["harness", "install"], env)
    assert yaml.safe_load(state.read_text())["status"] == "CONFLICT"

    assert not list(root.glob("commands/aips-*.md"))
    assert (root / "opencode.jsonc").read_bytes() == jsonc


def native_guard_cases(base):
    root = base / "playground"
    root.mkdir(parents=True)
    new_asset = root / "cat.svg"
    empty = {"task": {"classification": {"domain": "creative", "intent": "create", "effect": "filesystem_write"}},
             "intelligence": {"readiness": "PARTIAL"}, "freshness": {"status": "UNKNOWN"}, "fail_policy": {"mode": "soft"}}
    decision = native_guard.evaluate_write(tool="write", resources=[str(new_asset)], root=str(root), manifest=empty)
    assert decision["decision"] == "ALLOW" and decision["level"] == "L1", decision
    assert native_guard.evaluate_write(tool="edit", resources=[str(new_asset)], root=str(root), manifest=empty)["decision"] == "ALLOW"
    outside = base / "outside.svg"
    outside.write_text("safe")
    assert native_guard.evaluate_write(tool="write", resources=[str(outside)], root=str(root), manifest=empty)["decision"] == "DENY"
    link = root / "linked.svg"
    link.symlink_to(outside)
    assert native_guard.evaluate_write(tool="write", resources=[str(link)], root=str(root), manifest=empty)["decision"] == "DENY"
    ready = {"task": {"classification": {"domain": "software", "intent": "modify", "effect": "filesystem_write"}},
             "intelligence": {"readiness": "READY"}, "freshness": {"status": "CURRENT"}, "fail_policy": {"mode": "soft"},
             "instruction_resolution": {"requires_resolution": False}}
    git_root = base / "repo"
    git_root.mkdir()
    subprocess.run(["git", "init", "-q", str(git_root)], check=True)
    target = git_root / "src.py"
    assert native_guard.evaluate_write(tool="edit", resources=[str(target)], root=str(git_root), manifest=ready)["decision"] == "ALLOW"
    ready["freshness"] = {"status": "STALE"}
    assert native_guard.evaluate_write(tool="edit", resources=[str(target)], root=str(git_root), manifest=ready)["decision"] == "DENY"
    ready["freshness"] = {"status": "CURRENT"}
    assert native_guard.evaluate_write(tool="external_action", resources=[str(target)], root=str(git_root), manifest=ready)["level"] == "L3"
    assert native_guard.evaluate_shell(command="git status --short", cwd=str(git_root), root=str(git_root))["decision"] == "ALLOW"
    for command in ("rm -f x", "cat file > out", "find . -delete", "git push origin main", "echo ok; rm x", "sed -i s/a/b/ x"):
        assert native_guard.evaluate_shell(command=command, cwd=str(git_root), root=str(git_root))["decision"] == "DENY", command
    for command in (
        "find . -fprint /tmp/aips-out",
        "grep -f /etc/passwd src.py",
        "git --git-dir=/tmp/other/.git status",
        "git -c alias.status=!touch\u0020owned status",
        "rg --pre=sh -n secret .",
    ):
        assert native_guard.evaluate_shell(command=command, cwd=str(git_root), root=str(git_root))["decision"] == "DENY", command
    assert native_guard.evaluate_shell(command="cat /etc/passwd", cwd=str(git_root), root=str(git_root))["decision"] == "DENY"
    assert native_guard.evaluate_shell(command="ls ../outside", cwd=str(git_root), root=str(git_root))["decision"] == "DENY"
    diag = native_guard.evaluate_shell(command="aips creative preflight --project . --bundle creative.yaml", cwd=str(root), root=str(root))
    assert diag["decision"] == "ALLOW" and diag["reason_code"] == "shell_aips_readonly"
    assert native_guard.evaluate_shell(command="aips creative execute --project . --bundle creative.yaml", cwd=str(root), root=str(root))["reason_code"] == "shell_aips_command_unsupported"
    assert native_guard.evaluate_shell(command="aips creative trace --limit 20", cwd=str(root), root=str(root))["decision"] == "ALLOW"
    assert native_guard.evaluate_shell(command="python3 -c print(1)", cwd=str(root), root=str(root))["decision"] == "DENY"


def creative_profile_cases(base):
    project = base / "playground"
    project.mkdir(parents=True)
    (project / "cat.svg").write_text("<svg/>")
    (project / "ignored.png").symlink_to(base / "outside.png")
    env_cache = base / "cache"
    with patch.dict(os.environ, {"XDG_CACHE_HOME": str(env_cache)}):
        profile = creative_profile.scan(project)
        assert profile["mode"] == "EPHEMERAL" and profile["asset_count"] == 1
        cache = Path(profile["cache"])
        assert cache.is_relative_to(env_cache) and cache.stat().st_mode & 0o777 == 0o600
        assert not (project / ".ai").exists()
        (project / "cat-v1.svg").write_text("<svg/>")
        suggestion = creative_profile.next_version(project, "cat.svg")
        assert suggestion == {"status": "AVAILABLE", "path": "cat-v2.svg", "created": False, "overwrite": False}
        assert not (project / "cat-v2.svg").exists()


def trace_cases(base):
    base.mkdir(parents=True)
    path = base / "events.jsonl"
    path.write_text(json.dumps({"runtime": "opencode", "event": "context", "status": "delivered", "session": "0123456789abcdef"}) + "\n")
    result = opencode_trace.read_events(path)
    assert result["events"] == [{"runtime": "opencode", "event": "context", "status": "delivered", "session": "0123456789abcdef"}]
    path.write_text(json.dumps({"runtime": "opencode", "event": "context", "status": "delivered", "session": "secret prompt text"}) + "\n")
    assert opencode_trace.read_events(path)["events"] == []
    path.write_text(json.dumps({"runtime": "opencode", "event": "context", "status": "delivered", "prompt": "private"}) + "\n")
    assert opencode_trace.read_events(path)["events"] == [], "trace reader accepted a non-allowlisted field"
    path.write_text(json.dumps({"runtime": "opencode", "event": "permission", "decision": "ALLOW", "session_root_source": "location_directory", "project_mode": "EPHEMERAL", "project": "0123456789abcdef"}) + "\n")
    assert opencode_trace.read_events(path)["events"][0]["session_root_source"] == "location_directory"
    path.write_text(json.dumps({"runtime": "opencode", "event": "creative_execution", "decision": "ALLOW", "provider": "mflux_local", "operation": "generate", "duration_ms": 900, "project": "0123456789abcdef", "reason_code": "creative_tool_result"}) + "\n")
    assert opencode_trace.read_events(path)["events"][0]["provider"] == "mflux_local"
    path.write_text(json.dumps({"runtime": "opencode", "event": "creative_execution", "decision": "ALLOW", "provider": "mflux_local", "operation": "generate", "prompt": "private"}) + "\n")
    assert opencode_trace.read_events(path)["events"] == [], "creative trace accepted prompt content"
    try:
        opencode_trace.read_events(path, 101)
    except ValueError:
        pass
    else:
        raise AssertionError("trace query limit was not enforced")


def classification_cases():
    cases = {
        "討論角色配色，不要產生任何素材": "discuss",
        "規劃角色風格，先討論方向": "plan",
        "生成角色 SVG": "create",
        "修改既有角色圖片": "modify",
        "查看現有角色 SVG": "read",
    }
    for prompt, expected in cases.items():
        result = turn_intent.classify_task(prompt)
        assert result["intent"] == expected, (prompt, result)
    assert turn_intent.classify_task("討論角色配色，不要產生任何素材")["effect"] == "chat_only"


def main():
    plugin_source = (ROOT / "harness/adapters/opencode/plugin.ts").read_text(encoding="utf-8")
    assert 'ctx.tool.transform((editor)' in plugin_source and 'name: "creative_execution"' in plugin_source
    assert 'enum: ["prepare", "preflight", "execute"]' in plugin_source
    assert 'classification.intent !== "create"' in plugin_source and '"creative", "prepare"' in plugin_source
    assert 'identity_features' in plugin_source and '"--identity-feature"' in plugin_source
    assert 'toolContext.signal' in plugin_source and 'shell: false' in plugin_source
    desired = projection.skill_files()
    assert len(desired) == 27 and desired == projection.skill_files()
    for text in desired.values():
        assert "aips-source-sha256" in text
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        ownership_cases(base / "files")
        instruction_cases(base / "blocks")
        cli_cases(base / "cli")
        native_guard_cases(base / "guard")
        creative_profile_cases(base / "creative")
        trace_cases(base / "trace")
        classification_cases()
    print("OpenCode lifecycle PASS: native projections, V2 plugin ownership, conflicts, drift, interrupted writes, path confinement, L0-L3 direct-action guard, bounded Shell policy, CLI install/doctor/uninstall, MCP JSONC preservation")


if __name__ == "__main__":
    main()
