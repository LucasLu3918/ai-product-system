#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[2]


def run(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, check=check)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=root, check=check)


def configure_git(root: Path) -> None:
    git(root, "config", "user.email", "aips@example.invalid")
    git(root, "config", "user.name", "AIPS Migration Evidence")


def sentinel_validator(system: Path) -> None:
    (system / "tests" / "validate_repository.py").write_text(
        "print('LEGACY MIGRATION FIXTURE VALIDATION PASSED')\n",
        encoding="utf-8",
    )


def system_fixture(base: Path, name: str) -> tuple[Path, Path]:
    system = base / f"{name}-system"
    remote = base / f"{name}-remote.git"
    shutil.copytree(
        ROOT,
        system,
        ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.pyc"),
    )
    sentinel_validator(system)
    git(system, "init", "-q")
    git(system, "branch", "-m", "main")
    configure_git(system)
    git(system, "add", "-A")
    git(system, "commit", "-qm", "legacy system baseline")
    run(["git", "clone", "--bare", str(system), str(remote)], check=True)
    git(system, "remote", "add", "origin", str(remote))
    return system, remote


def remote_commit(remote: Path, base: Path, name: str, mutate: Callable[[Path], None]) -> str:
    updater = base / name
    run(["git", "clone", "-q", str(remote), str(updater)], check=True)
    configure_git(updater)
    mutate(updater)
    git(updater, "add", "-A")
    git(updater, "commit", "-qm", name)
    git(updater, "push", "-q", "origin", "main")
    return git(updater, "rev-parse", "HEAD").stdout.strip()


def next_patch(version: str) -> str:
    major, minor, patch = [int(x) for x in version.strip().split(".")]
    return f"{major}.{minor}.{patch + 1}"


def make_fake_venv(system: Path) -> None:
    py = system / ".venv" / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text(
        f"""#!{sys.executable}
import os
import sys
if len(sys.argv) >= 3 and sys.argv[1:3] == ["-m", "pip"]:
    raise SystemExit(0)
os.execv({sys.executable!r}, [{sys.executable!r}] + sys.argv[1:])
""",
        encoding="utf-8",
    )
    py.chmod(0o755)


def make_runtime(path: Path, name: str, body: str = "#!/usr/bin/env bash\nexit 0\n") -> None:
    target = path / name
    target.write_text(body, encoding="utf-8")
    target.chmod(0o755)


def runtime_env(base: Path, *, installed_system: Path | None = None) -> dict[str, str]:
    home = base / "home"
    config = base / "config"
    bin_home = base / "bin-home"
    fake_bin = base / "fake-bin"
    home.mkdir(parents=True, exist_ok=True)
    config.mkdir(parents=True, exist_ok=True)
    fake_bin.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(config),
            "AIPS_BIN_HOME": str(bin_home),
            "PATH": f"{fake_bin}:{env.get('PATH', '')}",
        }
    )
    if installed_system is not None:
        aips_home = config / "aips"
        aips_home.mkdir(parents=True, exist_ok=True)
        (aips_home / "system-dir").write_text(str(installed_system) + "\n", encoding="utf-8")
    return env


def cli(system: Path, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return run(["bash", str(system / "bin" / "aips"), *args], env=env)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def installed_legacy_preflight_migrates_to_managed_harness() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        base = Path(tmp)
        system, remote = system_fixture(base, "installed")
        make_fake_venv(system)
        env = runtime_env(base / "runtime")
        home = Path(env["HOME"])
        fake_bin = base / "runtime" / "fake-bin"

        (home / ".claude").mkdir(parents=True)
        claude = home / ".claude" / "CLAUDE.md"
        user_owned = "# user-owned legacy instructions\nKeep my local workflow.\n"
        claude.write_text(user_owned, encoding="utf-8")

        make_runtime(fake_bin, "codex")
        make_runtime(fake_bin, "claude")
        gemini_script = """#!/usr/bin/env bash
state="$HOME/.fake-gemini-extension"
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

        installed = cli(system, ["install"], env)
        require(installed.returncode == 0, f"legacy install setup failed: {installed.stdout} {installed.stderr}")
        require(user_owned.strip() in claude.read_text(encoding="utf-8"), "initial managed composition lost user-owned Claude instructions")
        system_dir_marker = Path(env["XDG_CONFIG_HOME"]) / "aips" / "system-dir"
        require(system_dir_marker.is_file(), "installed AIPS system marker missing")

        project = base / "product"
        project.mkdir()
        old_version = (system / "VERSION").read_text(encoding="utf-8").strip()
        upgraded_version = next_patch(old_version)
        updated_harness_marker = "AIPS_V0171_UPDATED_HARNESS_MARKER"

        def upgrade(updater: Path) -> None:
            (updater / "VERSION").write_text(upgraded_version + "\n", encoding="utf-8")
            adapter = updater / "harness" / "adapters" / "claude-code" / "CLAUDE.md"
            adapter.write_text(adapter.read_text(encoding="utf-8") + f"\n{updated_harness_marker}\n", encoding="utf-8")
            cli_path = updater / "bin" / "aips"
            text = cli_path.read_text(encoding="utf-8")
            needle = 'preflight_after_update() {\n  local project="$1"'
            replacement = needle + '\n  say "LEGACY_TO_MANAGED_NEW_CLI"'
            require(needle in text, "fixture could not mark updated preflight CLI")
            cli_path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")

        remote_sha = remote_commit(remote, base, "managed-harness-upgrade", upgrade)
        migrated = cli(system, ["preflight", str(project)], env)
        require(migrated.returncode == 0, f"legacy preflight migration failed: {migrated.stdout} {migrated.stderr}")
        require("LEGACY_TO_MANAGED_NEW_CLI" in migrated.stdout, "preflight did not re-exec the updated CLI")
        require("Refreshing AIPS Global Harness for the installed system" in migrated.stdout, "installed system did not refresh Global Harness after update")
        require((system / "VERSION").read_text(encoding="utf-8").strip() == upgraded_version, "system version did not fast-forward")
        require(git(system, "rev-parse", "HEAD").stdout.strip() == remote_sha, "system did not fast-forward to the upgraded commit")

        composed = claude.read_text(encoding="utf-8")
        require(user_owned.strip() in composed, "migration overwrote user-owned Claude instructions")
        require(updated_harness_marker in composed, "updated managed Harness block was not refreshed into Claude instructions")

        state = load_yaml(Path(env["XDG_CONFIG_HOME"]) / "aips" / "harness" / "adapters" / "claude-code.yaml")
        require(state.get("status") == "AUTOMATIC", "refreshed Claude adapter must remain AUTOMATIC")
        require(state.get("capability") in {"TURN_NATIVE", "CONTEXT_ALWAYS"}, "refreshed Claude adapter capability missing")


def collision_surfaces_manual_without_overwrite() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        base = Path(tmp)
        system, _ = system_fixture(base, "collision")
        env = runtime_env(base / "runtime")
        fake_bin = base / "runtime" / "fake-bin"
        calls = Path(env["HOME"]) / ".gemini-calls"
        gemini = f"""#!/usr/bin/env bash
printf '%s\\n' "$*" >> {str(calls)!r}
if [ "${{1:-}}" = extensions ] && [ "${{2:-}}" = list ]; then
  echo aips-global-harness
fi
exit 0
"""
        make_runtime(fake_bin, "gemini", gemini)

        result = cli(system, ["harness", "install"], env)
        require(result.returncode == 0, f"conflict-aware Harness install failed: {result.stdout} {result.stderr}")
        state_path = Path(env["XDG_CONFIG_HOME"]) / "aips" / "harness" / "adapters" / "gemini-cli.yaml"
        state = load_yaml(state_path)
        require(state.get("status") == "CONFLICT", "foreign Gemini integration collision must report CONFLICT")
        require(state.get("capability") == "MANUAL", "collision must downgrade to MANUAL capability")
        call_text = calls.read_text(encoding="utf-8")
        require("extensions list" in call_text, "collision detection did not inspect Gemini extensions")
        require("extensions link" not in call_text, "foreign Gemini integration was overwritten/relinked")


def plain_checkout_does_not_register_harness() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        base = Path(tmp)
        system, _ = system_fixture(base, "checkout")
        env = runtime_env(base / "runtime")
        project = base / "product"
        project.mkdir()
        fake_bin = base / "runtime" / "fake-bin"
        make_runtime(fake_bin, "codex")
        make_runtime(fake_bin, "claude")
        make_runtime(fake_bin, "gemini")

        config_aips = Path(env["XDG_CONFIG_HOME"]) / "aips"
        require(not (config_aips / "system-dir").exists(), "plain checkout fixture unexpectedly looks installed")
        result = cli(system, ["preflight", str(project)], env)
        require(result.returncode == 0, f"plain checkout preflight failed: {result.stdout} {result.stderr}")
        require("Refreshing AIPS Global Harness" not in result.stdout, "plain checkout preflight must not refresh/register Harness")
        require(not (config_aips / "harness").exists(), "plain checkout implicitly created Global Harness state")
        require(not (project / ".ai").exists(), "plain checkout preflight must keep project EPHEMERAL")


def main() -> int:
    installed_legacy_preflight_migrates_to_managed_harness()
    collision_surfaces_manual_without_overwrite()
    plain_checkout_does_not_register_harness()
    print("legacy_harness_migration_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
