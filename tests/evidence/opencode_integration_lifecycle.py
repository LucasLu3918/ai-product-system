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
import opencode_skill_projection as projection


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
    fake.write_text("#!/bin/sh\nprintf '99.0.0\\n'\n")
    run(cli + ["harness", "install"], env)
    assert yaml.safe_load(state.read_text())["status"] == "CONFLICT"
    assert not list(root.glob("skills/*/SKILL.md")), "unknown version installed projections"
    fake.write_text("#!/bin/sh\nexit 1\n")
    run(cli + ["harness", "install"], env)
    assert yaml.safe_load(state.read_text())["status"] == "CONFLICT"

    assert not list(root.glob("commands/aips-*.md"))
    assert (root / "opencode.jsonc").read_bytes() == jsonc


def main():
    desired = projection.skill_files()
    assert len(desired) == 27 and desired == projection.skill_files()
    for text in desired.values():
        assert "aips-source-sha256" in text
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        ownership_cases(base / "files")
        instruction_cases(base / "blocks")
        cli_cases(base / "cli")
    print("OpenCode lifecycle PASS: native projections, ownership, conflicts, drift, interrupted writes, path confinement, CLI install/doctor/uninstall, MCP JSONC preservation")


if __name__ == "__main__":
    main()
