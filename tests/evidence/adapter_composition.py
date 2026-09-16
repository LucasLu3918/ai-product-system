#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "scripts" / "manage_runtime_adapter.py"
CLI = ROOT / "bin" / "aips"


def run_manager(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MANAGER), *args],
        capture_output=True,
        text=True,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_runtime(path: Path, name: str) -> None:
    target = path / name
    target.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def helper_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "CLAUDE.md"
        source = root / "aips.md"
        snapshot = root / "owned.block"
        original = "# user rule\nkeep this exactly\n"
        target.write_text(original, encoding="utf-8")
        source.write_text("# aips rule\n", encoding="utf-8")

        installed = run_manager(
            "install-block",
            "--target", str(target),
            "--source", str(source),
            "--snapshot", str(snapshot),
        )
        require(installed.returncode == 0, f"managed block install failed: {installed.stderr}")
        installed_text = target.read_text(encoding="utf-8")
        require(original.strip() in installed_text, "existing user instructions were not preserved")
        require("AIPS-MANAGED-BEGIN" in installed_text, "AIPS managed block missing")

        removed = run_manager(
            "uninstall-block",
            "--target", str(target),
            "--snapshot", str(snapshot),
        )
        require(removed.returncode == 0, f"managed block uninstall failed: {removed.stderr}")
        require(target.read_text(encoding="utf-8") == original, "uninstall did not restore original user file bytes")

        installed = run_manager(
            "install-block",
            "--target", str(target),
            "--source", str(source),
            "--snapshot", str(snapshot),
        )
        require(installed.returncode == 0, "second managed block install failed")
        edited = target.read_text(encoding="utf-8").replace("# aips rule", "# aips rule manually edited")
        target.write_text(edited, encoding="utf-8")
        conflict = run_manager(
            "uninstall-block",
            "--target", str(target),
            "--snapshot", str(snapshot),
        )
        require(conflict.returncode != 0, "modified managed block must not be silently removed")
        conflict_doc = json.loads(conflict.stdout)
        require(conflict_doc.get("status") == "CONFLICT", "modified managed block must report CONFLICT")
        require("manually edited" in target.read_text(encoding="utf-8"), "modified managed block was not preserved")


def harness_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home"
        config = root / "config"
        fakebin = root / "fakebin"
        aips_bin = root / "aips-bin"
        (home / ".codex").mkdir(parents=True)
        (home / ".claude").mkdir(parents=True)
        fakebin.mkdir()
        make_runtime(fakebin, "codex")
        make_runtime(fakebin, "claude")

        codex_file = home / ".codex" / "AGENTS.md"
        claude_file = home / ".claude" / "CLAUDE.md"
        codex_original = "# codex user rule\n"
        claude_original = "# claude user rule\n"
        codex_file.write_text(codex_original, encoding="utf-8")
        claude_file.write_text(claude_original, encoding="utf-8")

        settings = home / ".claude" / "settings.json"
        user_hook = {"hooks": [{"type": "command", "command": "user-hook"}]}
        original_settings = {"permissions": {"allow": ["Read"]}, "hooks": {"PreToolUse": [user_hook]}}
        settings.write_text(json.dumps(original_settings, indent=2) + "\n", encoding="utf-8")

        env = dict(os.environ)
        env["HOME"] = str(home)
        env["XDG_CONFIG_HOME"] = str(config)
        env["AIPS_BIN_HOME"] = str(aips_bin)
        env["PATH"] = str(fakebin) + os.pathsep + env.get("PATH", "")

        installed = subprocess.run(
            ["bash", str(CLI), "harness", "install"],
            env=env,
            capture_output=True,
            text=True,
        )
        require(installed.returncode == 0, f"harness install failed: {installed.stdout} {installed.stderr}")

        codex_text = codex_file.read_text(encoding="utf-8")
        claude_text = claude_file.read_text(encoding="utf-8")
        require(codex_original.strip() in codex_text and "AIPS-MANAGED-BEGIN" in codex_text, "Codex managed composition failed")
        require(claude_original.strip() in claude_text and "AIPS-MANAGED-BEGIN" in claude_text, "Claude managed composition failed")

        harness_home = config / "aips" / "harness"
        ownership = harness_home / "installation.yaml"
        require(ownership.is_file(), "Harness ownership manifest missing")

        codex_state = load_yaml(harness_home / "adapters" / "codex.yaml")
        claude_state = load_yaml(harness_home / "adapters" / "claude-code.yaml")
        require(codex_state.get("status") == "AUTOMATIC", "Codex installation status must be AUTOMATIC")
        require(codex_state.get("capability") == "CONTEXT_ALWAYS", "Codex capability must be CONTEXT_ALWAYS")
        require(codex_state.get("governance_enforcement") == "ADVISORY", "Codex enforcement must remain ADVISORY")
        require(claude_state.get("status") == "AUTOMATIC", "Claude installation status must be AUTOMATIC")
        require(claude_state.get("capability") == "TURN_NATIVE", "Claude verified hook capability must be TURN_NATIVE")
        require(claude_state.get("governance_enforcement") == "TOOL_GUARDED", "Claude verified guard must be TOOL_GUARDED")

        settings_doc = json.loads(settings.read_text(encoding="utf-8"))
        require(settings_doc.get("permissions") == {"allow": ["Read"]}, "unrelated Claude settings changed")
        require(user_hook in settings_doc.get("hooks", {}).get("PreToolUse", []), "unrelated PreToolUse hook was replaced")
        require("UserPromptSubmit" in settings_doc.get("hooks", {}), "AIPS UserPromptSubmit hook missing")
        require(
            any(
                "AIPS_MANAGED_HOOK=1" in str(h.get("command", ""))
                for group in settings_doc.get("hooks", {}).get("PreToolUse", [])
                for h in group.get("hooks", [])
            ),
            "AIPS governance PreToolUse hook missing",
        )

        removed = subprocess.run(
            ["bash", str(CLI), "harness", "uninstall"],
            env=env,
            capture_output=True,
            text=True,
        )
        require(removed.returncode == 0, f"harness uninstall failed: {removed.stdout} {removed.stderr}")
        require(codex_file.read_text(encoding="utf-8") == codex_original, "Codex user file was not restored")
        require(claude_file.read_text(encoding="utf-8") == claude_original, "Claude user file was not restored")
        settings_doc = json.loads(settings.read_text(encoding="utf-8"))
        require(settings_doc.get("permissions") == {"allow": ["Read"]}, "Claude permissions changed on uninstall")
        require(settings_doc.get("hooks", {}).get("PreToolUse") == [user_hook], "unrelated Claude hook not preserved")
        require("UserPromptSubmit" not in settings_doc.get("hooks", {}), "AIPS Claude prompt hook not removed")
        require(not harness_home.exists(), "successful harness uninstall must remove AIPS ownership state")


def main() -> int:
    helper_contract()
    harness_contract()
    print("adapter_composition evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
