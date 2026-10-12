"""Exercise the public Skill list CLI from outside the AIPS checkout."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from skill_index import generate
from skills_cli import collect
from native_skill_projection import _source_package


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(cwd: Path, *args: str, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["AIPS_VALIDATION_PYTHON"] = sys.executable
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [str(ROOT / "bin/aips"), "skills", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    expected_catalog = generate(ROOT)["skills"]
    expected_ids = sorted(expected_catalog)
    expected = collect(locale="zh-TW", include_upstream=False, capability=None, trigger=None)

    with tempfile.TemporaryDirectory() as temporary:
        cwd = Path(temporary)
        before = (ROOT / "skills/INDEX.yaml").read_bytes()

        installed_bin = cwd / "installed-bin"
        installed_bin.mkdir()
        installed_cli = installed_bin / "aips"
        installed_cli.symlink_to(ROOT / "bin/aips")

        result = run(cwd, "list", "--format", "json")
        require(result.returncode == 0, f"JSON list failed: {result.stderr}")
        listed = json.loads(result.stdout)
        require(listed == expected, "JSON list differs from canonical Skill metadata and locale")
        require(len(listed) == 48 and {item["id"] for item in listed} == set(expected_ids),
                "default list must include all active AIPS Skills")
        require(listed == sorted(listed, key=lambda item: (item["category"], item["source"], item["id"])),
                "default list order must be stable by category and Skill id")
        require(listed[0]["locale"] == "zh-TW", "default locale must be Traditional Chinese")

        env = dict(os.environ)
        env["AIPS_VALIDATION_PYTHON"] = sys.executable
        result = subprocess.run(
            [str(installed_cli), "skills", "list", "--format", "json"],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        require(result.returncode == 0, f"installed CLI symlink failed: {result.stderr}")
        require(json.loads(result.stdout) == expected,
                "installed CLI symlink did not resolve the same canonical Skill catalog")

        capability = expected[0]["capability"]
        result = run(cwd, "list", "--capability", capability, "--format", "json")
        require(result.returncode == 0, f"capability filter failed: {result.stderr}")
        filtered = json.loads(result.stdout)
        require(filtered and all(row["capability"] == capability for row in filtered),
                "capability filter did not match exactly")

        trigger = expected[0]["triggers"][0]
        result = run(cwd, "list", "--trigger", trigger, "--format", "json")
        require(result.returncode == 0, f"trigger filter failed: {result.stderr}")
        filtered = json.loads(result.stdout)
        require(filtered and all(trigger in row["triggers"] for row in filtered),
                "trigger filter did not match exactly")

        result = run(cwd, "list", "--capability", "no-such-capability", "--format", "json")
        require(result.returncode == 0 and json.loads(result.stdout) == [],
                "an empty result should remain a successful empty list")

        result = run(cwd, "list")
        require(result.returncode == 0, f"text list failed: {result.stderr}")
        require("| 技能 | 來源 / 狀態 | 用途 | AIPS 對應 |" in result.stdout,
                "text output is missing the Traditional Chinese table header")
        require(expected[0]["id"] in result.stdout and expected[0]["description"] in result.stdout,
                "text output is missing Skill name or description")

        for args in (("--help",), ("list", "--help")):
            result = run(cwd, *args)
            require(result.returncode == 0, f"help route failed for {args}: {result.stderr}")

        result = run(cwd)
        require(result.returncode == 0 and "Usage: aips skills list" in result.stdout,
                "group help must be shown when no Skill subcommand is supplied")

        env = dict(os.environ)
        env["AIPS_VALIDATION_PYTHON"] = sys.executable
        result = subprocess.run(
            [str(ROOT / "bin/aips"), "help"], cwd=cwd, env=env,
            capture_output=True, text=True, check=False,
        )
        require(result.returncode == 0 and "aips skills list" in result.stdout,
                "root help must include the Skill command")

        result = run(cwd, "unknown")
        require(result.returncode != 0 and "Unknown skills command" in result.stderr,
                "unknown Skill subcommands must fail with a group-specific error")

        result = run(cwd, "list", "--unknown-option")
        require(result.returncode != 0 and "unrecognized arguments" in result.stderr,
                "unknown list arguments must fail")

        result = run(cwd, "list", "--include-upstream", "--format", "json")
        require(result.returncode == 0, f"upstream list failed: {result.stderr}")
        expanded = json.loads(result.stdout)
        require(len(expanded) == 86, "upstream view must add exactly 38 reviewed records")
        upstream_grill = next((item for item in expanded if item["id"] == "grill-me" and item["source"] == "upstream"), None)
        require(upstream_grill and upstream_grill["status"] == "workflow",
                "upstream grill-me must be shown with its workflow disposition")
        require("## 工程" in run(cwd, "list").stdout,
                "default human-readable list must group skills under Traditional Chinese categories")

        isolated_home = cwd / "native-home"
        isolated_config = cwd / "native-config"
        isolated_env = {"HOME": str(isolated_home), "XDG_CONFIG_HOME": str(isolated_config)}
        isolated_home.mkdir()
        managed_id = expected_ids[0]
        installed = run(cwd, "install", managed_id, "--host", "codex", "--host", "gemini", "--format", "json", env_overrides=isolated_env)
        require(installed.returncode == 0, f"native multi-host install failed: {installed.stderr}")
        install_rows = json.loads(installed.stdout)["results"]
        require([row["status"] for row in install_rows] == ["INSTALLED", "SHARED"],
                "Codex and Gemini must share one interoperable native Skill installation")
        shared_path = isolated_home / ".agents/skills" / managed_id / "SKILL.md"
        require(shared_path.is_file(), "Codex/Gemini native Skill was not written to the shared discovery path")
        repeated = run(cwd, "install", managed_id, "--host", "codex", "--format", "json", env_overrides=isolated_env)
        require(repeated.returncode == 0 and json.loads(repeated.stdout)["results"][0]["status"] == "CURRENT",
                "repeated native installation must be idempotent")
        manifest = json.loads((isolated_config / "aips/skills/ownership.json").read_text(encoding="utf-8"))
        require(manifest["artifacts"][0]["hosts"] == ["codex", "gemini"],
                "ownership manifest must record both hosts without duplicating the shared Skill")
        removed_codex = run(cwd, "uninstall", managed_id, "--host", "codex", "--format", "json", env_overrides=isolated_env)
        require(removed_codex.returncode == 0 and json.loads(removed_codex.stdout)["results"][0]["status"] == "RETAINED_SHARED" and shared_path.is_file(),
                "removing Codex association must preserve the still-shared Gemini Skill")
        removed_gemini = run(cwd, "uninstall", managed_id, "--host", "gemini", "--format", "json", env_overrides=isolated_env)
        require(removed_gemini.returncode == 0 and json.loads(removed_gemini.stdout)["results"][0]["status"] == "REMOVED" and not shared_path.exists(),
                "removing the final shared host must remove only the AIPS-owned Skill")

        unowned_id = expected_ids[1]
        unowned_files, _ = _source_package(ROOT, unowned_id)
        unowned_dir = isolated_home / ".agents/skills" / unowned_id
        unowned_dir.mkdir(parents=True)
        (unowned_dir / "SKILL.md").write_bytes(unowned_files["SKILL.md"])
        unowned = run(cwd, "install", unowned_id, "--host", "codex", "--format", "json", env_overrides=isolated_env)
        require(unowned.returncode == 0 and json.loads(unowned.stdout)["results"][0]["status"] == "ALREADY_PRESENT_UNOWNED",
                "an identical pre-existing native Skill must not be rewritten or claimed")

        conflicting_id = expected_ids[2]
        conflicting_dir = isolated_home / ".agents/skills" / conflicting_id
        conflicting_dir.mkdir(parents=True)
        existing_bytes = b"user-owned skill\n"
        (conflicting_dir / "SKILL.md").write_bytes(existing_bytes)
        conflict = run(cwd, "install", conflicting_id, "--host", "codex", "--format", "json", env_overrides=isolated_env)
        require(conflict.returncode != 0 and json.loads(conflict.stdout)["results"][0]["status"] == "CONFLICT" and (conflicting_dir / "SKILL.md").read_bytes() == existing_bytes,
                "a different pre-existing native Skill must be preserved and reported as conflict")

        legacy_path = isolated_config / "aips/commands/projections/codex/aips-grill-me.md"
        legacy_path.parent.mkdir(parents=True)
        legacy_content = "legacy AIPS-owned command projection\n"
        legacy_path.write_text(legacy_content, encoding="utf-8")
        legacy_manifest = isolated_config / "aips/commands/ownership.yaml"
        legacy_record = {"version": 1, "artifacts": [{"command_id": "aips.grill-me", "host": "codex", "path": str(legacy_path), "generated_digest": hashlib.sha256(legacy_content.encode("utf-8")).hexdigest()}]}
        legacy_manifest.write_text(json.dumps(legacy_record), encoding="utf-8")
        command_install = subprocess.run([str(ROOT / "bin/aips"), "commands", "install", "aips.grill-me", "--host", "codex", "--format", "json"], cwd=cwd, env={**os.environ, "AIPS_VALIDATION_PYTHON": sys.executable, **isolated_env}, capture_output=True, text=True, check=False)
        grill_path = isolated_home / ".agents/skills/grill-me/SKILL.md"
        require(command_install.returncode == 0 and grill_path.is_file() and not legacy_path.exists(),
                f"portable grill-me command was not migrated to a Codex native Skill: {command_install.stdout} {command_install.stderr}")
        grill_text = grill_path.read_text(encoding="utf-8")
        require("name: grill-me" in grill_text and "Invoke this interview only when the user explicitly" in grill_text,
                "native grill-me Skill must include host metadata and canonical behavior guidance")
        other_command = subprocess.run([str(ROOT / "bin/aips"), "commands", "install", "aips.plan", "--host", "codex", "--format", "json"], cwd=cwd, env={**os.environ, "AIPS_VALIDATION_PYTHON": sys.executable, **isolated_env}, capture_output=True, text=True, check=False)
        other_command_path = isolated_home / ".agents/skills/aips-plan/SKILL.md"
        require(other_command.returncode == 0 and other_command_path.is_file(),
                "second portable command was not installed for selective-uninstall coverage")
        command_repeat = subprocess.run([str(ROOT / "bin/aips"), "commands", "install", "aips.grill-me", "--host", "codex", "--format", "json"], cwd=cwd, env={**os.environ, "AIPS_VALIDATION_PYTHON": sys.executable, **isolated_env}, capture_output=True, text=True, check=False)
        require(command_repeat.returncode == 0 and json.loads(command_repeat.stdout)["results"][0]["status"] == "CURRENT",
                "repeated portable command installation must remain idempotent")
        gemini_install = subprocess.run([str(ROOT / "bin/aips"), "commands", "install", "aips.grill-me", "--host", "gemini", "--format", "json"], cwd=cwd, env={**os.environ, "AIPS_VALIDATION_PYTHON": sys.executable, **isolated_env}, capture_output=True, text=True, check=False)
        claude_install = subprocess.run([str(ROOT / "bin/aips"), "commands", "install", "aips.grill-me", "--host", "claude", "--format", "json"], cwd=cwd, env={**os.environ, "AIPS_VALIDATION_PYTHON": sys.executable, **isolated_env}, capture_output=True, text=True, check=False)
        require(gemini_install.returncode == 0 and json.loads(gemini_install.stdout)["results"][0]["status"] == "SHARED",
                "Gemini must join Codex's shared native Skill without creating a duplicate")
        require(claude_install.returncode == 0 and (isolated_home / ".claude/skills/grill-me/SKILL.md").is_file(),
                "portable grill-me command was not installed to Claude Code's native Skill path")
        grill_path.write_text(grill_text + "\nuser edit\n", encoding="utf-8")
        (grill_path.parent / "notes.txt").write_text("keep me", encoding="utf-8")
        claude_remove = subprocess.run([str(ROOT / "bin/aips"), "commands", "uninstall", "--host", "claude", "--format", "json"], cwd=cwd, env={**os.environ, "AIPS_VALIDATION_PYTHON": sys.executable, **isolated_env}, capture_output=True, text=True, check=False)
        require(claude_remove.returncode == 0 and not (isolated_home / ".claude/skills/grill-me/SKILL.md").exists(),
                "Claude uninstall must remove only its recorded native Skill")
        codex_remove = subprocess.run([str(ROOT / "bin/aips"), "commands", "uninstall", "aips.grill-me", "--host", "codex", "--format", "json"], cwd=cwd, env={**os.environ, "AIPS_VALIDATION_PYTHON": sys.executable, **isolated_env}, capture_output=True, text=True, check=False)
        require(codex_remove.returncode == 0 and "RETAINED_SHARED" in codex_remove.stdout and grill_path.is_file(),
                "removing Codex must preserve the shared Gemini Skill")
        gemini_remove = subprocess.run([str(ROOT / "bin/aips"), "commands", "uninstall", "aips.grill-me", "--host", "gemini", "--format", "json"], cwd=cwd, env={**os.environ, "AIPS_VALIDATION_PYTHON": sys.executable, **isolated_env}, capture_output=True, text=True, check=False)
        require(gemini_remove.returncode != 0 and "CONFLICT_PRESERVED" in gemini_remove.stdout and grill_path.is_file() and (grill_path.parent / "notes.txt").read_text(encoding="utf-8") == "keep me",
                "targeted final uninstall must preserve a modified native Skill and extra user resources")
        require(other_command_path.is_file(),
                "uninstalling grill-me must leave another Portable Command installed for the same host")
        remove_other = subprocess.run([str(ROOT / "bin/aips"), "commands", "uninstall", "aips.plan", "--host", "codex", "--format", "json"], cwd=cwd, env={**os.environ, "AIPS_VALIDATION_PYTHON": sys.executable, **isolated_env}, capture_output=True, text=True, check=False)
        require(remove_other.returncode == 0 and not other_command_path.exists(),
                "targeted uninstall must remove the selected Portable Command")

        workspace = cwd / "workspace"
        workspace.mkdir()
        workspace_install = run(cwd, "install", managed_id, "--host", "claude", "--scope", "workspace", "--project", str(workspace), "--format", "json", env_overrides=isolated_env)
        workspace_path = workspace / ".claude/skills" / managed_id / "SKILL.md"
        require(workspace_install.returncode == 0 and workspace_path.is_file(),
                "workspace install must use Claude Code's native .claude/skills discovery path")
        foreign_status = run(cwd, "status", "--host", "claude", "--format", "json", env_overrides=isolated_env)
        require(foreign_status.returncode == 0 and json.loads(foreign_status.stdout)["results"] == [],
                "status from another project must not report a different workspace's install as conflicting")
        foreign_remove = run(cwd, "uninstall", managed_id, "--host", "claude", "--format", "json", env_overrides=isolated_env)
        require(foreign_remove.returncode == 0 and workspace_path.is_file(),
                "uninstall from another project must not remove a workspace Skill")
        workspace_status = run(cwd, "status", "--host", "claude", "--scope", "workspace", "--project", str(workspace), "--format", "json", env_overrides=isolated_env)
        require(workspace_status.returncode == 0 and json.loads(workspace_status.stdout)["results"][0]["status"] == "CURRENT",
                "workspace ownership must remain verifiable outside the target project cwd")
        workspace_remove = run(cwd, "uninstall", managed_id, "--host", "claude", "--scope", "workspace", "--project", str(workspace), "--format", "json", env_overrides=isolated_env)
        require(workspace_remove.returncode == 0 and not workspace_path.exists(),
                "workspace uninstall must remove only the matching AIPS-owned projection")

        require((ROOT / "skills/INDEX.yaml").read_bytes() == before,
                "listing Skills must not modify the generated index")

    print("Skill CLI lifecycle PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
