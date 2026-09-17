#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tempfile

import yaml

from install_preflight_lifecycle import (
    cli,
    make_env,
    remote_commit,
    require,
    system_fixture,
)


def make_runtime(path: Path, name: str, body: str) -> None:
    target = path / name
    target.write_text(body, encoding="utf-8")
    target.chmod(0o755)


def next_patch(version: str) -> str:
    major, minor, patch = version.strip().split(".")
    return f"{int(major)}.{int(minor)}.{int(patch) + 1}"


def patch_updated_cli(system: Path, marker: str) -> None:
    cli_path = system / "bin" / "aips"
    text = cli_path.read_text(encoding="utf-8")
    needle = 'preflight_after_update() {\n  local project="$1"'
    require(needle in text, "fixture could not locate updated preflight CLI entry")
    cli_path.write_text(text.replace(needle, needle + f'\n  say "{marker}"', 1), encoding="utf-8")


def installed_legacy_refresh() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, remote = system_fixture(base, "legacy-harness")
        env = make_env(base / "runtime", base / "validation.log")
        home = Path(env["HOME"])
        config = Path(env["XDG_CONFIG_HOME"])
        fake_bin = base / "runtime" / "fake-bin"
        project = base / "project"
        project.mkdir()

        # Simulate an older installed AIPS system. The system-dir marker is the
        # canonical signal used by the current CLI to distinguish an install
        # from a plain repository checkout.
        install_state = config / "aips"
        install_state.mkdir(parents=True, exist_ok=True)
        (install_state / "system-dir").write_text(str(system) + "\n", encoding="utf-8")

        user_codex = home / ".codex" / "AGENTS.md"
        user_codex.parent.mkdir(parents=True, exist_ok=True)
        user_text = "# user-owned instructions\nNever remove this line.\n"
        user_codex.write_text(user_text, encoding="utf-8")

        make_runtime(fake_bin, "codex", "#!/usr/bin/env bash\nexit 0\n")

        # A foreign Gemini registration deliberately collides with the AIPS
        # extension id. It must remain untouched and surface as CONFLICT/MANUAL.
        gemini_calls = home / ".fake-gemini-calls"
        gemini_script = f'''#!/usr/bin/env bash
printf '%s\\n' "$*" >> {str(gemini_calls)!r}
if [ "${{1:-}}" = extensions ] && [ "${{2:-}}" = list ]; then
  echo aips-global-harness
  exit 0
fi
if [ "${{1:-}}" = extensions ] && [ "${{2:-}}" = link ]; then
  exit 9
fi
exit 0
'''
        make_runtime(fake_bin, "gemini", gemini_script)

        legacy = cli(system, ["harness", "install"], env)
        require(legacy.returncode == 0, f"legacy Harness setup failed: {legacy.stdout} {legacy.stderr}")
        require(user_text.strip() in user_codex.read_text(encoding="utf-8"), "legacy Harness setup overwrote user Codex instructions")

        gemini_state_path = config / "aips" / "harness" / "adapters" / "gemini-cli.yaml"
        gemini_state = yaml.safe_load(gemini_state_path.read_text(encoding="utf-8")) or {}
        require(gemini_state.get("status") == "CONFLICT", "foreign Gemini registration must surface CONFLICT")
        require(gemini_state.get("capability") == "MANUAL", "foreign Gemini registration must require MANUAL handling")
        require("extensions link" not in gemini_calls.read_text(encoding="utf-8"), "colliding Gemini registration must not be overwritten")

        old_version = (system / "VERSION").read_text(encoding="utf-8").strip()
        upgraded_version = next_patch(old_version)
        refresh_marker = "LEGACY_HARNESS_REFRESHED_BY_UPDATED_CLI"
        adapter_marker = "LEGACY_MIGRATION_ADAPTER_REFRESH_MARKER"

        def mutate(updater: Path) -> None:
            (updater / "VERSION").write_text(upgraded_version + "\n", encoding="utf-8")
            patch_updated_cli(updater, refresh_marker)
            adapter = updater / "harness" / "adapters" / "codex" / "AGENTS.md"
            adapter.write_text(adapter.read_text(encoding="utf-8") + f"\n{adapter_marker}\n", encoding="utf-8")

        remote_commit(remote, base, "legacy-harness-upgrade", mutate)
        upgraded = cli(system, ["preflight", str(project)], env)
        require(upgraded.returncode == 0, f"legacy preflight migration failed: {upgraded.stdout} {upgraded.stderr}")
        require(refresh_marker in upgraded.stdout, "old preflight must re-exec the updated CLI")
        require("Refreshing AIPS Global Harness for the installed system" in upgraded.stdout, "updated CLI must refresh managed Harness for an installed system")
        require((system / "VERSION").read_text(encoding="utf-8").strip() == upgraded_version, "legacy preflight did not update AIPS system version")

        composed = user_codex.read_text(encoding="utf-8")
        require(user_text.strip() in composed, "Harness refresh did not preserve user-owned Codex instructions")
        require(adapter_marker in composed, "Harness refresh did not compose the updated managed adapter content")

        refreshed_state = yaml.safe_load(gemini_state_path.read_text(encoding="utf-8")) or {}
        require(refreshed_state.get("status") == "CONFLICT", "Harness refresh must preserve collision truth as CONFLICT")
        require(refreshed_state.get("capability") == "MANUAL", "Harness refresh must preserve MANUAL collision handling")
        require("extensions link" not in gemini_calls.read_text(encoding="utf-8"), "Harness refresh must not overwrite a foreign Gemini registration")


def plain_checkout_does_not_register_harness() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, remote = system_fixture(base, "plain-checkout")
        env = make_env(base / "runtime", base / "validation.log")
        config = Path(env["XDG_CONFIG_HOME"])
        fake_bin = base / "runtime" / "fake-bin"
        project = base / "project"
        project.mkdir()
        make_runtime(fake_bin, "codex", "#!/usr/bin/env bash\nexit 0\n")

        old_version = (system / "VERSION").read_text(encoding="utf-8").strip()
        upgraded_version = next_patch(old_version)
        marker = "PLAIN_CHECKOUT_UPDATED_CLI"

        def mutate(updater: Path) -> None:
            (updater / "VERSION").write_text(upgraded_version + "\n", encoding="utf-8")
            patch_updated_cli(updater, marker)

        remote_commit(remote, base, "plain-checkout-upgrade", mutate)
        result = cli(system, ["preflight", str(project)], env)
        require(result.returncode == 0, f"plain checkout preflight failed: {result.stdout} {result.stderr}")
        require(marker in result.stdout, "plain checkout preflight must still re-exec the updated CLI")
        require(not (config / "aips" / "system-dir").exists(), "plain checkout must not become an installed AIPS system implicitly")
        require(not (config / "aips" / "harness").exists(), "plain checkout preflight must not register Global Harness implicitly")


def main() -> int:
    installed_legacy_refresh()
    plain_checkout_does_not_register_harness()
    print("legacy_harness_migration_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
