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
    assert len(native) == 49
    for path in native:
        meta = yaml.safe_load(path.read_text().split("---", 2)[1])
        assert meta["name"] == path.parent.name and meta["description"]
    native_commands = list(root.glob("commands/aips-*.md"))
    assert len(native_commands) == 4
    grill_me = root / "commands/aips-grill-me.md"
    assert grill_me.is_file() and "explicit" in grill_me.read_text(encoding="utf-8").lower()
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
    stale_decision = native_guard.evaluate_write(tool="edit", resources=[str(target)], root=str(git_root), manifest=ready)
    assert stale_decision["decision"] == "ALLOW" and "stale but advisory" in stale_decision["reason"], stale_decision
    ready["fail_policy"] = {"mode": "closed", "reasons": ["intelligence_stale"]}
    assert native_guard.evaluate_write(tool="edit", resources=[str(target)], root=str(git_root), manifest=ready)["decision"] == "ALLOW"
    ready["fail_policy"] = {"mode": "closed", "reasons": ["intelligence_stale", "unresolved_authority_conflict"]}
    assert native_guard.evaluate_write(tool="edit", resources=[str(target)], root=str(git_root), manifest=ready)["decision"] == "DENY"
    ready["fail_policy"] = {"mode": "soft"}
    ready["instruction_resolution"] = {"requires_resolution": True}
    assert native_guard.evaluate_write(tool="edit", resources=[str(target)], root=str(git_root), manifest=ready)["decision"] == "DENY"
    ready["instruction_resolution"] = {"requires_resolution": False}
    ready["intelligence"] = {"readiness": "PARTIAL"}
    assert native_guard.evaluate_write(tool="edit", resources=[str(target)], root=str(git_root), manifest=ready)["decision"] == "DENY"
    ready["intelligence"] = {"readiness": "READY"}
    ready["freshness"] = {"status": "UNKNOWN"}
    assert native_guard.evaluate_write(tool="edit", resources=[str(target)], root=str(git_root), manifest=ready)["decision"] == "DENY"
    ready["freshness"] = {"status": "STALE"}
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

        destination = base / "destination"
        (destination / "assets").mkdir(parents=True)
        candidate = creative_profile.import_candidate(project, "cat.svg", destination, "assets/cat.svg")
        assert candidate["status"] == "READY" and candidate["overwrite"] is False
        assert candidate["source"]["sha256"] == __import__("hashlib").sha256(b"<svg/>").hexdigest()
        assert candidate["destination"]["state"] == "ABSENT" and not (destination / "assets/cat.svg").exists()
        candidate_file = Path(candidate["candidate_file"])
        assert candidate_file.is_relative_to(env_cache) and candidate_file.stat().st_mode & 0o777 == 0o600
        assert b"<svg/>" not in candidate_file.read_bytes(), "candidate cache must not contain asset bytes"

        tampered = json.loads(candidate_file.read_text(encoding="utf-8"))
        tampered["destination"]["path"] = "../escape.svg"
        tampered_path = base / "tampered.json"
        tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
        expect_blocked(lambda: creative_profile.import_asset(tampered_path, candidate["candidate_sha256"]))

        (project / "cat.svg").write_text("<svg changed/>", encoding="utf-8")
        expect_blocked(lambda: creative_profile.import_asset(candidate_file, candidate["candidate_sha256"]))
        (project / "cat.svg").write_text("<svg/>", encoding="utf-8")
        fresh = creative_profile.import_candidate(project, "cat.svg", destination, "assets/cat.svg")
        (destination / "assets" / "cat.svg").write_text("keep me", encoding="utf-8")
        expect_blocked(lambda: creative_profile.import_asset(Path(fresh["candidate_file"]), fresh["candidate_sha256"]))
        assert (destination / "assets" / "cat.svg").read_text(encoding="utf-8") == "keep me"
        (destination / "assets" / "cat.svg").unlink()

        accepted = creative_profile.import_candidate(project, "cat.svg", destination, "assets/cat.svg")
        imported = creative_profile.import_asset(Path(accepted["candidate_file"]), accepted["candidate_sha256"])
        assert imported["status"] == "IMPORTED" and imported["created"] is True and imported["overwrite"] is False
        assert (destination / "assets" / "cat.svg").read_bytes() == b"<svg/>"
        expect_blocked(lambda: creative_profile.import_asset(Path(accepted["candidate_file"]), accepted["candidate_sha256"]))

        conflict = creative_profile.import_candidate(project, "cat.svg", destination, "assets/cat.svg")
        assert conflict["status"] == "CONFLICT" and conflict["destination"]["existing_sha256"]
        expect_blocked(lambda: creative_profile.import_asset(Path(conflict["candidate_file"]), conflict["candidate_sha256"]))
        expect_blocked(lambda: creative_profile.import_candidate(project, "../outside.png", destination, "assets/outside.png"))
        expect_blocked(lambda: creative_profile.import_candidate(project, "ignored.png", destination, "assets/ignored.png"))
        legacy_destination = base / "legacy-destination"
        (legacy_destination / "assets").mkdir(parents=True)
        legacy_candidate = creative_profile.import_candidate(project, "cat.svg", legacy_destination, "assets/cat.svg")
        legacy_doc = json.loads(Path(legacy_candidate["candidate_file"]).read_text(encoding="utf-8"))
        legacy_doc["destination"].pop("mode")
        legacy_doc.pop("candidate_sha256")
        legacy_doc["candidate_sha256"] = __import__("hashlib").sha256(creative_profile._candidate_body(legacy_doc)).hexdigest()
        legacy_file = base / "legacy-candidate.json"
        legacy_file.write_text(json.dumps(legacy_doc), encoding="utf-8")
        legacy_import = creative_profile.import_asset(legacy_file, legacy_doc["candidate_sha256"])
        assert legacy_import["status"] == "IMPORTED" and (legacy_destination / "assets" / "cat.svg").read_bytes() == b"<svg/>"
        git_destination = base / "git-destination"
        git_destination.mkdir()
        subprocess.run(["git", "init", "-q", str(git_destination)], check=True)
        (git_destination / "tracked.txt").write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(git_destination), "add", "tracked.txt"], check=True)
        git_index = git_destination / ".git" / "index"
        index_before_import = git_index.read_bytes()
        expect_blocked(lambda: creative_profile.import_candidate(project, "cat.svg", git_destination, "cat.svg"))
        (git_destination / "assets").mkdir()
        explicit_git = creative_profile.import_candidate(
            project, "cat.svg", git_destination, "assets/cat.svg", allow_git_destination=True
        )
        assert explicit_git["status"] == "READY"
        assert explicit_git["destination"]["mode"] == "GIT_OPT_IN"
        assert explicit_git["overwrite"] is False
        explicit_git_file = Path(explicit_git["candidate_file"])
        imported_git = creative_profile.import_asset(explicit_git_file, explicit_git["candidate_sha256"])
        assert imported_git["status"] == "IMPORTED" and imported_git["created"] is True
        assert (git_destination / "assets" / "cat.svg").read_bytes() == b"<svg/>"
        assert git_index.read_bytes() == index_before_import, "import must not change the Git index"
        expect_blocked(lambda: creative_profile.import_asset(explicit_git_file, explicit_git["candidate_sha256"]))
        expect_blocked(lambda: creative_profile.import_candidate(
            project, "cat.svg", git_destination, "assets/.git/cat.svg", allow_git_destination=True
        ))
        non_git_opt_in = base / "non-git-opt-in"
        (non_git_opt_in / "assets").mkdir(parents=True)
        expect_blocked(lambda: creative_profile.import_candidate(
            project, "cat.svg", non_git_opt_in, "assets/cat.svg", allow_git_destination=True
        ))
        nested_destination = git_destination / "assets"
        expect_blocked(lambda: creative_profile.import_candidate(
            project, "cat.svg", nested_destination, "nested.svg", allow_git_destination=True
        ))
        expect_blocked(lambda: creative_profile.import_candidate(
            git_destination, "assets/cat.svg", git_destination, "assets/from-git.svg", allow_git_destination=True
        ))

        cli_destination = base / "cli-destination"
        (cli_destination / "assets").mkdir(parents=True)
        cli_git_destination = base / "cli-git-destination"
        cli_git_destination.mkdir()
        subprocess.run(["git", "init", "-q", str(cli_git_destination)], check=True)
        (cli_git_destination / "tracked.txt").write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(cli_git_destination), "add", "tracked.txt"], check=True)
        cli_git_index = cli_git_destination / ".git" / "index"
        cli_index_before_import = cli_git_index.read_bytes()
        (cli_git_destination / "assets").mkdir()
        cli_env = {**os.environ, "XDG_CACHE_HOME": str(env_cache), "AIPS_VALIDATION_PYTHON": sys.executable}
        cli = ROOT / "bin" / "aips"
        rejected_cli_proposal = run([str(cli), "creative", "import-candidate", "--source-project", str(project), "--source", "cat.svg", "--destination-project", str(cli_git_destination), "--target", "assets/rejected.svg"], cli_env, ok=False)
        assert rejected_cli_proposal.returncode != 0
        proposal_git = run([str(cli), "creative", "import-candidate", "--source-project", str(project), "--source", "cat.svg", "--destination-project", str(cli_git_destination), "--target", "assets/cat.svg", "--allow-git-destination"], cli_env)
        proposal_git_doc = json.loads(proposal_git.stdout)
        imported_git_cli = run([str(cli), "creative", "import", "--candidate", proposal_git_doc["candidate_file"], "--accept-hash", proposal_git_doc["candidate_sha256"]], cli_env)
        assert json.loads(imported_git_cli.stdout)["status"] == "IMPORTED"
        assert (cli_git_destination / "assets" / "cat.svg").read_bytes() == b"<svg/>"
        assert cli_git_index.read_bytes() == cli_index_before_import, "CLI import must not change the Git index"
        proposal = run([str(cli), "creative", "import-candidate", "--source-project", str(project), "--source", "cat.svg", "--destination-project", str(cli_destination), "--target", "assets/cat.svg"], cli_env)
        proposal_doc = json.loads(proposal.stdout)
        imported_cli = run([str(cli), "creative", "import", "--candidate", proposal_doc["candidate_file"], "--accept-hash", proposal_doc["candidate_sha256"]], cli_env)
        assert json.loads(imported_cli.stdout)["status"] == "IMPORTED"
        assert (cli_destination / "assets" / "cat.svg").read_bytes() == b"<svg/>"

    dispatch = (ROOT / "scripts" / "aips_cli" / "dispatch.sh").read_text(encoding="utf-8")
    assert "scan|next-version|import-candidate|import)" in dispatch


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
    path.write_text(json.dumps({
        "runtime": "opencode", "event": "context", "status": "unavailable",
        "reason_code": "context_compaction_over_budget", "context_original_bytes": 50000,
        "context_projection_bytes": 14000,
        "context_largest_sections": [{"section": "freshness", "bytes": 13000}],
    }) + "\n")
    diagnostic = opencode_trace.read_events(path)["events"][0]
    assert diagnostic["reason_code"] == "context_compaction_over_budget"
    assert diagnostic["context_largest_sections"] == [{"section": "freshness", "bytes": 13000}]
    path.write_text(json.dumps({
        "runtime": "opencode", "event": "context", "status": "unavailable",
        "reason_code": "context_compaction_over_budget", "context_largest_sections": [
            {"section": "freshness", "bytes": 100, "value": "private"},
        ],
    }) + "\n")
    assert opencode_trace.read_events(path)["events"] == [], "trace accepted unbounded section metadata"
    try:
        opencode_trace.read_events(path, 101)
    except ValueError:
        pass
    else:
        raise AssertionError("trace query limit was not enforced")


def context_budget_cases():
    module_url = (ROOT / "harness/adapters/opencode/context_diagnostics.mjs").as_uri()
    script = f'''import assert from "node:assert/strict";
const {{compactManifest, formatContextFailure, MAX_CONTEXT_BYTES}} = await import({json.dumps(module_url)});
const base = {{
  version: 1,
  runtime: "opencode",
  project: {{mode: "ATTACHED"}},
  task: {{classification: {{domain: "software", intent: "modify"}}, readiness: "L2"}},
  context: {{system_protocol_routes: {{category: "general_mutation", protocols: [{{id: "change_impact"}}]}}, intelligence_topics: [], retrieval: {{status: "READY"}}}},
  intelligence: {{readiness: "READY", review: "UNREVIEWED"}},
  freshness: {{status: "CURRENT", reasons: []}},
  fail_policy: {{mode: "closed", reasons: []}},
}};
const compacted = compactManifest({{...base, unrelated: "x".repeat(MAX_CONTEXT_BYTES + 100)}});
assert.equal(compacted.truncated, true);
assert.ok(Buffer.byteLength(compacted.body) <= MAX_CONTEXT_BYTES);
assert.equal(compacted.reasonCode, undefined);
const overflow = compactManifest({{
  ...base,
  unrelated: "x".repeat(MAX_CONTEXT_BYTES * 2),
  freshness: {{status: "STALE", reasons: Array.from({{length: 600}}, (_, index) => `source_changed:item-${{index}}-` + "y".repeat(80))}},
}});
assert.equal(overflow.body, "", "irreducible overflow must remain fail-closed");
assert.equal(overflow.reasonCode, "context_compaction_over_budget");
assert.ok(overflow.originalBytes > MAX_CONTEXT_BYTES);
assert.ok(overflow.compactBytes > MAX_CONTEXT_BYTES);
assert.equal(overflow.largestSections[0].section, "freshness");
const message = formatContextFailure(overflow);
assert.match(message, /context_compaction_over_budget/);
assert.match(message, new RegExp(String(overflow.compactBytes)));
assert.match(message, /aips intelligence refresh-plan/);
assert.match(message, /writes remain denied/i);
assert.doesNotMatch(message, /source_changed:item-/);
'''
    result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT, text=True, capture_output=True, timeout=30, check=False)
    assert result.returncode == 0, (result.stdout, result.stderr)


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
    assert 'enum: ["prepare", "configure", "discover", "preflight", "execute", "generate-set", "review-assist", "quality-check", "feedback", "repair", "compare", "quality-loop"]' in plugin_source
    assert 'classification.intent !== "create"' in plugin_source and '"creative", "prepare"' in plugin_source
    assert 'ctx.session.hook("prompt"' in plugin_source and 'creativeAdmissions' in plugin_source and 'slice(-64)' not in plugin_source
    assert 'max_outputs: remainingOutputs' in plugin_source, "a fresh prompt reset already consumed output budget"
    assert 'identity_features' in plugin_source and '"--identity-feature"' in plugin_source
    assert 'toolContext.signal' in plugin_source and 'shell: false' in plugin_source
    desired = projection.skill_files()
    assert len(desired) == 49 and desired == projection.skill_files()
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
        context_budget_cases()
        classification_cases()
    print("OpenCode lifecycle PASS: native projections, V2 plugin ownership, conflicts, drift, interrupted writes, path confinement, L0-L3 direct-action guard, bounded Shell policy, CLI install/doctor/uninstall, MCP JSONC preservation")


if __name__ == "__main__":
    main()
