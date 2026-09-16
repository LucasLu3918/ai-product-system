#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "bin" / "aips"
HOOKS = ROOT / "harness" / "adapters" / "gemini-cli" / "hooks" / "hooks.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_runtime(path: Path, name: str, body: str = "#!/usr/bin/env bash\nexit 0\n") -> None:
    target = path / name
    target.write_text(body, encoding="utf-8")
    target.chmod(0o755)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def harness_install_and_truth() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        fake_bin = base / "fake-bin"
        config = base / "config"
        bin_home = base / "bin-home"
        project = base / "project"
        home.mkdir()
        fake_bin.mkdir()
        project.mkdir()
        (home / ".claude").mkdir()
        (home / ".gemini").mkdir()

        claude_file = home / ".claude" / "CLAUDE.md"
        claude_original = "# user-owned claude instructions\n"
        claude_file.write_text(claude_original, encoding="utf-8")

        gemini_user = home / ".gemini" / "GEMINI.md"
        gemini_settings = home / ".gemini" / "settings.json"
        gemini_original = "# user-owned gemini instructions\n"
        settings_original = '{"theme":"user"}\n'
        gemini_user.write_text(gemini_original, encoding="utf-8")
        gemini_settings.write_text(settings_original, encoding="utf-8")

        make_runtime(fake_bin, "codex")
        make_runtime(fake_bin, "claude")
        gemini_script = """#!/usr/bin/env bash
state="$HOME/.fake-gemini-extension"
calls="$HOME/.fake-gemini-calls"
printf '%s\n' "$*" >> "$calls"
if [ "${1:-}" = extensions ]; then
  case "${2:-}" in
    list) [ -f "$state" ] && echo aips-global-harness; exit 0 ;;
    link) touch "$state"; exit 0 ;;
    uninstall) rm -f "$state"; exit 0 ;;
  esac
fi
exit 0
"""
        make_runtime(fake_bin, "gemini", gemini_script)

        env = dict(os.environ)
        env.update({
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(config),
            "AIPS_BIN_HOME": str(bin_home),
            "PATH": f"{fake_bin}:{env.get('PATH', '')}",
        })

        installed = subprocess.run(["bash", str(CLI), "harness", "install"], env=env, capture_output=True, text=True)
        require(installed.returncode == 0, f"harness install failed: {installed.stdout} {installed.stderr}")

        harness_home = config / "aips" / "harness"
        states = {
            name: load_yaml(harness_home / "adapters" / f"{name}.yaml")
            for name in ("codex", "claude-code", "gemini-cli")
        }
        require(states["codex"].get("status") == "AUTOMATIC", "Codex install status must be AUTOMATIC")
        require(states["codex"].get("capability") == "CONTEXT_ALWAYS", "Codex capability must be CONTEXT_ALWAYS")
        require(states["codex"].get("governance_enforcement") == "ADVISORY", "Codex enforcement must be ADVISORY")
        require(states["claude-code"].get("capability") == "TURN_NATIVE", "Claude capability must be TURN_NATIVE when hook is verified")
        require(states["claude-code"].get("governance_enforcement") == "TOOL_GUARDED", "Claude enforcement must be TOOL_GUARDED")
        require(states["gemini-cli"].get("status") == "AUTOMATIC", "Gemini install status must be AUTOMATIC")
        require(states["gemini-cli"].get("capability") == "TURN_NATIVE", "Gemini capability must be TURN_NATIVE")
        require(states["gemini-cli"].get("governance_enforcement") == "TOOL_GUARDED", "Gemini enforcement must be TOOL_GUARDED")

        calls = (home / ".fake-gemini-calls").read_text(encoding="utf-8")
        require("extensions link " in calls, "Gemini adapter must use official extension link mechanism")
        require((home / ".fake-gemini-extension").exists(), "Gemini extension registration missing")

        ownership = (harness_home / "installation.yaml").read_text(encoding="utf-8")
        require("runtime_registration" in ownership and "aips-global-harness" in ownership, "Gemini AIPS ownership not recorded")
        require(gemini_user.read_text(encoding="utf-8") == gemini_original, "Gemini user GEMINI.md was overwritten")
        require(gemini_settings.read_text(encoding="utf-8") == settings_original, "Gemini user settings were overwritten")
        require(claude_original.strip() in claude_file.read_text(encoding="utf-8"), "Claude user content was not preserved")

        hooks = json.loads(HOOKS.read_text(encoding="utf-8"))
        require("BeforeAgent" in (hooks.get("hooks") or {}), "Gemini extension must define BeforeAgent")
        before_agent = hooks["hooks"]["BeforeAgent"]
        hook_commands = [
            h.get("command", "")
            for group in before_agent
            for h in group.get("hooks", [])
        ]
        require(any("aips-turn-context.sh" in cmd for cmd in hook_commands), "BeforeAgent must invoke AIPS Turn Context")

        resolved = subprocess.run(
            ["bash", str(CLI), "harness", "resolve", "--runtime", "gemini-cli", "--project", str(project), "--format", "json"],
            env=env, capture_output=True, text=True,
        )
        require(resolved.returncode == 0, f"Gemini harness resolve failed: {resolved.stdout} {resolved.stderr}")
        doc = json.loads(resolved.stdout)
        require(doc.get("project", {}).get("mode") == "EPHEMERAL", "project without .ai must remain EPHEMERAL")
        require(not (project / ".ai").exists(), "harness resolve must not auto-attach project")
        require(doc.get("runtime", {}).get("capability") == "TURN_NATIVE", "resolved Gemini capability mismatch")
        require(doc.get("runtime", {}).get("governance_enforcement") == "TOOL_GUARDED", "resolved Gemini enforcement mismatch")

        removed = subprocess.run(["bash", str(CLI), "harness", "uninstall"], env=env, capture_output=True, text=True)
        require(removed.returncode == 0, f"harness uninstall failed: {removed.stdout} {removed.stderr}")
        require(not (home / ".fake-gemini-extension").exists(), "Gemini extension was not unregistered")
        calls = (home / ".fake-gemini-calls").read_text(encoding="utf-8")
        require("extensions uninstall aips-global-harness" in calls, "Gemini uninstall must target only AIPS namespace")
        require(gemini_user.read_text(encoding="utf-8") == gemini_original, "Gemini user GEMINI.md changed on uninstall")
        require(gemini_settings.read_text(encoding="utf-8") == settings_original, "Gemini user settings changed on uninstall")


def failed_uninstall_retry() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        fake_bin = base / "fake-bin"
        config = base / "config"
        bin_home = base / "bin-home"
        home.mkdir()
        fake_bin.mkdir()

        gemini_script = """#!/usr/bin/env bash
state="$HOME/.fake-gemini-extension"
fail="$HOME/.fake-gemini-fail-uninstall"
if [ "${1:-}" = extensions ]; then
  case "${2:-}" in
    list) [ -f "$state" ] && echo aips-global-harness; exit 0 ;;
    link) touch "$state"; exit 0 ;;
    uninstall) [ -f "$fail" ] && exit 9; rm -f "$state"; exit 0 ;;
  esac
fi
exit 0
"""
        make_runtime(fake_bin, "gemini", gemini_script)
        env = dict(os.environ)
        env.update({
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(config),
            "AIPS_BIN_HOME": str(bin_home),
            "PATH": f"{fake_bin}:{env.get('PATH', '')}",
        })

        installed = subprocess.run(["bash", str(CLI), "harness", "install"], env=env, capture_output=True, text=True)
        require(installed.returncode == 0, "Gemini recovery setup install failed")
        harness_home = config / "aips" / "harness"
        require(harness_home.exists(), "Harness ownership state missing before uninstall")

        (home / ".fake-gemini-fail-uninstall").touch()
        failed = subprocess.run(["bash", str(CLI), "harness", "uninstall"], env=env, capture_output=True, text=True)
        require(failed.returncode != 0, "Uninstall must fail when AIPS-owned Gemini registration cannot be removed")
        require(harness_home.exists(), "Failed uninstall must preserve ownership state for retry")
        require((home / ".fake-gemini-extension").exists(), "Failed uninstall must not lose the remaining registration")

        (home / ".fake-gemini-fail-uninstall").unlink()
        retry = subprocess.run(["bash", str(CLI), "harness", "uninstall"], env=env, capture_output=True, text=True)
        require(retry.returncode == 0, f"Uninstall retry failed: {retry.stdout} {retry.stderr}")
        require(not harness_home.exists(), "Successful retry must clear AIPS ownership state")
        require(not (home / ".fake-gemini-extension").exists(), "Successful retry must unregister Gemini extension")


def main() -> int:
    harness_install_and_truth()
    failed_uninstall_retry()
    print("harness_runtime_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
