#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, check=check)


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=root, check=check)


def configure_git(root: Path) -> None:
    git(root, "config", "user.email", "aips@example.invalid")
    git(root, "config", "user.name", "AIPS Evidence")


def sentinel_validator(system: Path) -> None:
    target = system / "tests" / "validate_repository.py"
    target.write_text(
        """from pathlib import Path
import os
marker = os.environ.get("AIPS_VALIDATION_MARKER")
if marker:
    path = Path(marker)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write("validated\\n")
print("FIXTURE VALIDATION PASSED")
""",
        encoding="utf-8",
    )


def system_fixture(base: Path, name: str) -> tuple[Path, Path]:
    system = base / f"{name}-system"
    remote = base / f"{name}-remote.git"
    shutil.copytree(
        ROOT,
        system,
        ignore=shutil.ignore_patterns(".git", ".venv", ".venv.*", "__pycache__", "*.pyc"),
    )
    sentinel_validator(system)
    git(system, "init", "-q")
    git(system, "branch", "-m", "main")
    configure_git(system)
    git(system, "add", "-A")
    git(system, "commit", "-qm", "fixture baseline")
    run(["git", "clone", "--bare", str(system), str(remote)], check=True)
    git(system, "remote", "add", "origin", str(remote))
    return system, remote


def remote_commit(remote: Path, base: Path, name: str, mutate) -> str:
    updater = base / name
    run(["git", "clone", "-q", str(remote), str(updater)], check=True)
    configure_git(updater)
    mutate(updater)
    git(updater, "add", "-A")
    git(updater, "commit", "-qm", name)
    git(updater, "push", "-q", "origin", "main")
    return git(updater, "rev-parse", "HEAD").stdout.strip()


def make_env(base: Path, marker: Path, *, bin_home: Path | None = None) -> dict[str, str]:
    home = base / "home"
    config = base / "config"
    fake_bin = base / "fake-bin"
    home.mkdir(parents=True, exist_ok=True)
    fake_bin.mkdir(parents=True, exist_ok=True)
    for runtime in ("codex", "claude", "gemini"):
        p = fake_bin / runtime
        p.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        p.chmod(0o755)
    env = dict(os.environ)
    python_bin = str(Path(sys.executable).parent)
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(config),
        "AIPS_BIN_HOME": str(bin_home or (base / "bin-home")),
        "AIPS_VALIDATION_MARKER": str(marker),
        "PATH": f"{python_bin}:{fake_bin}:{env.get('PATH', '')}",
    })
    return env


def cli(system: Path, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return run(["bash", str(system / "bin" / "aips"), *args], env=env)


def init_product(base: Path) -> tuple[Path, Path, str, str]:
    project = base / "product"
    remote = base / "product-remote.git"
    project.mkdir()
    (project / "app.txt").write_text("local product\n", encoding="utf-8")
    git(project, "init", "-q")
    git(project, "branch", "-m", "main")
    configure_git(project)
    git(project, "add", "app.txt")
    git(project, "commit", "-qm", "product baseline")
    baseline = git(project, "rev-parse", "HEAD").stdout.strip()
    run(["git", "clone", "--bare", str(project), str(remote)], check=True)
    git(project, "remote", "add", "origin", str(remote))

    def mutate(updater: Path) -> None:
        (updater / "app.txt").write_text("remote product update\n", encoding="utf-8")

    remote_commit(remote, base, "product-updater", mutate)
    return project, remote, baseline, (project / "app.txt").read_text(encoding="utf-8")


def next_patch(version: str) -> str:
    parts = version.strip().split(".")
    return f"{int(parts[0])}.{int(parts[1])}.{int(parts[2]) + 1}"


def preflight_and_project_lifecycle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, remote = system_fixture(base, "preflight")
        marker = base / "validation.log"
        env = make_env(base / "runtime", marker)
        project, _, product_head, product_text = init_product(base)

        git(system, "switch", "-qc", "feature")
        wrong_branch = cli(system, ["preflight", str(project)], env)
        require(wrong_branch.returncode != 0 and "must be on 'main'" in wrong_branch.stderr, "Preflight must stop when system branch is not main")
        git(system, "switch", "-q", "main")

        dirty = system / "UNCOMMITTED_FIXTURE"
        dirty.write_text("dirty\n", encoding="utf-8")
        dirty_result = cli(system, ["preflight", str(project)], env)
        require(dirty_result.returncode != 0 and "local changes" in dirty_result.stderr, "Preflight must stop for dirty system worktree")
        dirty.unlink()

        first = cli(system, ["preflight", str(project)], env)
        require(first.returncode == 0, f"clean main preflight failed: {first.stdout} {first.stderr}")
        require("Project mode: EPHEMERAL" in first.stdout, "Preflight must report EPHEMERAL without .ai")
        require(not (project / ".ai").exists(), "Preflight must not auto-attach an EPHEMERAL project")
        require(not (system / ".venv").exists(), "Plain source preflight must not create a managed virtual environment")
        require(marker.exists(), "Preflight must validate the system")
        require(git(project, "rev-parse", "HEAD").stdout.strip() == product_head, "Preflight must not pull target product repository")
        require((project / "app.txt").read_text(encoding="utf-8") == product_text, "Preflight changed target product source")

        attached = cli(system, ["attach", str(project)], env)
        require(attached.returncode == 0 and (project / ".ai").is_dir(), f"attach failed: {attached.stdout} {attached.stderr}")
        status = cli(system, ["status", str(project)], env)
        require(status.returncode == 0 and "Project attached: yes" in status.stdout and "Project mode: ATTACHED" in status.stdout, "status must report attached provenance")

        old_version = (system / "VERSION").read_text(encoding="utf-8").strip()
        upgraded_version = next_patch(old_version)

        def system_update(updater: Path) -> None:
            (updater / "VERSION").write_text(upgraded_version + "\n", encoding="utf-8")
            cli_path = updater / "bin" / "aips"
            text = cli_path.read_text(encoding="utf-8")
            needle = 'preflight_after_update() {\n  local project="$1"'
            replacement = needle + '\n  say "UPDATED_CLI_MARKER"'
            require(needle in text, "fixture could not patch updated CLI marker")
            cli_path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")

        remote_sha = remote_commit(remote, base, "system-updater", system_update)
        upgraded = cli(system, ["preflight", str(project)], env)
        require(upgraded.returncode == 0, f"fast-forward preflight failed: {upgraded.stdout} {upgraded.stderr}")
        require("UPDATED_CLI_MARKER" in upgraded.stdout, "Preflight must re-enter the updated CLI after pull")
        require((system / "VERSION").read_text(encoding="utf-8").strip() == upgraded_version, "Preflight did not fast-forward system version")
        require(git(system, "rev-parse", "HEAD").stdout.strip() == remote_sha, "Preflight did not fast-forward to remote main")
        snapshot = yaml.safe_load((project / ".ai" / "SYSTEM.yaml").read_text(encoding="utf-8")) or {}
        system_snapshot = snapshot.get("system") or {}
        require(str(system_snapshot.get("version")) == upgraded_version, "Attached preflight did not refresh exact system version")
        require(str(system_snapshot.get("commit")) == remote_sha, "Attached preflight did not refresh exact system commit")
        require(git(project, "rev-parse", "HEAD").stdout.strip() == product_head, "Attached preflight pulled target product repository")

        detached = cli(system, ["detach", str(project)], env)
        require(detached.returncode == 0 and not (project / ".ai").exists(), f"detach failed: {detached.stdout} {detached.stderr}")
        archives = sorted(project.glob(".ai.detached-*"))
        require(len(archives) == 1, "Detach must preserve exactly one archived workspace")
        require((project / "app.txt").read_text(encoding="utf-8") == product_text, "Detach modified product source")

        blocked_attach = cli(system, ["attach", str(project)], env)
        require(blocked_attach.returncode != 0 and "detached AI workspace already exists" in blocked_attach.stderr, "Attach must stop when a detached workspace exists")

        archives[0].rename(project / ".ai")
        restored = cli(system, ["attach", str(project)], env)
        require(restored.returncode == 0 and (project / ".ai").exists(), "Documented detached-workspace restore must allow attach")

        bin_home = Path(env["AIPS_BIN_HOME"])
        bin_home.mkdir(parents=True, exist_ok=True)
        cli_link = bin_home / "aips"
        cli_link.symlink_to(system / "bin" / "aips")
        config_home = Path(env["XDG_CONFIG_HOME"]) / "aips"
        config_home.mkdir(parents=True, exist_ok=True)
        (config_home / "system-dir").write_text(str(system) + "\n", encoding="utf-8")
        external = config_home / "projects" / "preserve-me"
        external.mkdir(parents=True, exist_ok=True)
        (external / "data.txt").write_text("preserve\n", encoding="utf-8")
        venv = system / ".venv"
        venv.mkdir()
        (venv / "preserve.txt").write_text("preserve\n", encoding="utf-8")

        uninstalled = cli(system, ["uninstall"], env)
        require(uninstalled.returncode == 0, f"default uninstall failed: {uninstalled.stdout} {uninstalled.stderr}")
        require(not cli_link.exists(), "Default uninstall must remove AIPS-owned CLI symlink")
        require((project / ".ai").exists(), "Default uninstall must preserve project .ai workspace")
        require((external / "data.txt").exists(), "Default uninstall must preserve External Project Intelligence")
        require((venv / "preserve.txt").exists(), "Default uninstall must preserve system venv")
        require(system.exists() and (system / ".git").exists(), "Uninstall must preserve AIPS repository")

        explicit = cli(system, ["uninstall", "--remove-cache", "--remove-venv"], env)
        require(explicit.returncode == 0, f"explicit cleanup uninstall failed: {explicit.stdout} {explicit.stderr}")
        require(not (config_home / "projects").exists(), "--remove-cache must remove external cache")
        require(not venv.exists(), "--remove-venv must remove system venv")


def divergence_gate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, remote = system_fixture(base, "diverge")
        env = make_env(base / "runtime", base / "validation.log")
        project = base / "project"
        project.mkdir()

        (system / "local.txt").write_text("local\n", encoding="utf-8")
        git(system, "add", "local.txt")
        git(system, "commit", "-qm", "local divergence")

        def mutate(updater: Path) -> None:
            (updater / "remote.txt").write_text("remote\n", encoding="utf-8")

        remote_commit(remote, base, "diverge-updater", mutate)
        result = cli(system, ["preflight", str(project)], env)
        require(result.returncode != 0 and "diverged" in result.stderr, "Preflight must never auto merge/rebase divergent system history")


def major_version_gate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, remote = system_fixture(base, "major")
        marker = base / "validation.log"
        env = make_env(base / "runtime", marker)
        project = base / "project"
        project.mkdir()
        local_version = (system / "VERSION").read_text(encoding="utf-8").strip()
        major_version = f"{int(local_version.split('.')[0]) + 1}.0.0"

        def mutate(updater: Path) -> None:
            (updater / "VERSION").write_text(major_version + "\n", encoding="utf-8")

        remote_commit(remote, base, "major-updater", mutate)
        blocked = cli(system, ["preflight", str(project)], env)
        require(blocked.returncode != 0 and "Major version change detected" in blocked.stderr, "Major upgrade must require explicit allow-major")

        allowed = cli(system, ["preflight", str(project), "--allow-major"], env)
        require(allowed.returncode == 0, f"allowed major preflight failed: {allowed.stdout} {allowed.stderr}")
        require((system / "VERSION").read_text(encoding="utf-8").strip() == major_version, "--allow-major did not update system")
        require(marker.exists(), "Allowed major preflight must validate updated system")


def make_fake_venv(system: Path) -> None:
    py = system / ".venv" / "bin" / "python"
    py.parent.mkdir(parents=True)
    body = f"""#!{sys.executable}
import os
import sys
if len(sys.argv) >= 3 and sys.argv[1:3] == ["-m", "pip"]:
    raise SystemExit(0)
os.execv({sys.executable!r}, [{sys.executable!r}] + sys.argv[1:])
"""
    py.write_text(body, encoding="utf-8")
    py.chmod(0o755)


def make_repairing_fake_venv(system: Path, marker: Path) -> None:
    py = system / ".venv" / "bin" / "python"
    py.parent.mkdir(parents=True)
    body = f"""#!{sys.executable}
import os
from pathlib import Path
import sys
marker = Path({str(marker)!r})
if len(sys.argv) >= 3 and sys.argv[1:3] == ["-m", "pip"]:
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("repaired\\n", encoding="utf-8")
    raise SystemExit(0)
if len(sys.argv) >= 3 and sys.argv[1] == "-c" and "import yaml, mcp" in sys.argv[2] and not marker.exists():
    raise SystemExit(1)
os.execv({sys.executable!r}, [{sys.executable!r}] + sys.argv[1:])
"""
    py.write_text(body, encoding="utf-8")
    py.chmod(0o755)


def make_incompatible_fake_venv(system: Path) -> None:
    py = system / ".venv" / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    py.chmod(0o755)


def make_fake_python_creator(base: Path, marker: Path) -> Path:
    creator = base / "python3-compatible"
    runtime_body = f"""#!{sys.executable}
import os
from pathlib import Path
import sys
marker = Path({str(marker)!r})
if len(sys.argv) >= 3 and sys.argv[1:3] == ["-m", "pip"]:
    marker.write_text("installed\\n", encoding="utf-8")
    raise SystemExit(0)
if len(sys.argv) >= 3 and sys.argv[1] == "-c" and ("sys.version_info" in sys.argv[2] or "import yaml, mcp" in sys.argv[2]):
    raise SystemExit(0)
os.execv({sys.executable!r}, [{sys.executable!r}] + sys.argv[1:])
"""
    creator_body = f"""#!{sys.executable}
from pathlib import Path
import sys
if len(sys.argv) >= 3 and sys.argv[1:3] == ["-m", "venv"]:
    py = Path(sys.argv[3]) / "bin" / "python"
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text({runtime_body!r}, encoding="utf-8")
    py.chmod(0o755)
    raise SystemExit(0)
if len(sys.argv) >= 3 and sys.argv[1] == "-c" and "sys.version_info" in sys.argv[2]:
    raise SystemExit(0)
raise SystemExit(1)
"""
    creator.write_text(creator_body, encoding="utf-8")
    creator.chmod(0o755)
    return creator


def runtime_dependency_health_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, _ = system_fixture(base, "dependency-health")
        marker = base / "dependency-repaired"
        make_repairing_fake_venv(system, marker)
        env = make_env(base / "runtime", base / "validation.log")

        unhealthy = cli(system, ["doctor"], env)
        require(unhealthy.returncode != 0, "Doctor must fail when required runtime dependencies are incomplete")
        require(
            "runtime dependencies: INCOMPLETE" in unhealthy.stderr,
            "Doctor must identify incomplete PyYAML/MCP runtime dependencies",
        )

        config_home = Path(env["XDG_CONFIG_HOME"]) / "aips"
        config_home.mkdir(parents=True, exist_ok=True)
        (config_home / "system-dir").write_text(str(system) + "\n", encoding="utf-8")
        repaired = cli(system, ["update"], env)
        require(repaired.returncode == 0, f"Managed update dependency repair failed: {repaired.stdout} {repaired.stderr}")
        require(marker.exists(), "Managed update must reinstall missing runtime dependencies")
        require("AIPS runtime dependencies: repaired" in repaired.stdout, "Managed update must report dependency repair")

        healthy = cli(system, ["doctor"], env)
        require(healthy.returncode == 0, f"Doctor must pass after dependency repair: {healthy.stdout} {healthy.stderr}")
        require("runtime dependencies: OK (PyYAML, MCP)" in healthy.stdout, "Doctor must report healthy runtime dependencies")


def runtime_python_compatibility_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, _ = system_fixture(base, "python-compatibility")
        make_incompatible_fake_venv(system)
        dependency_marker = base / "dependencies-installed"
        creator = make_fake_python_creator(base, dependency_marker)
        env = make_env(base / "runtime", base / "validation.log")
        env["AIPS_PYTHON"] = str(creator)
        config_home = Path(env["XDG_CONFIG_HOME"]) / "aips"
        config_home.mkdir(parents=True, exist_ok=True)
        (config_home / "system-dir").write_text(str(system) + "\n", encoding="utf-8")

        repaired = cli(system, ["update"], env)
        require(repaired.returncode == 0, f"Unsupported managed Python repair failed: {repaired.stdout} {repaired.stderr}")
        require("unsupported Python" in repaired.stderr, "Repair must explain why the managed virtual environment is recreated")
        require(dependency_marker.exists(), "Recreated managed virtual environment must install runtime dependencies")
        venv = system / ".venv" / "bin" / "python"
        require(venv.exists(), "Recreated managed virtual environment Python is missing")


def cli_collision_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, _ = system_fixture(base, "install")
        make_fake_venv(system)

        regular_home = base / "regular-bin"
        regular_home.mkdir()
        regular = regular_home / "aips"
        regular.write_text("foreign cli\n", encoding="utf-8")
        env_regular = make_env(base / "regular-runtime", base / "regular-validation.log", bin_home=regular_home)
        regular_result = cli(system, ["install"], env_regular)
        require(regular_result.returncode != 0 and "not an AIPS symlink" in regular_result.stderr, "Regular CLI collision must stop install")
        require(regular.read_text(encoding="utf-8") == "foreign cli\n", "Regular CLI collision was overwritten or deleted")
        require(not (Path(env_regular["XDG_CONFIG_HOME"]) / "aips" / "system-dir").exists(), "Collision must not claim installation complete")
        require(not Path(env_regular["AIPS_VALIDATION_MARKER"]).exists(), "Collision must stop before validation/runtime install")

        foreign_home = base / "foreign-bin"
        foreign_home.mkdir()
        target = base / "foreign-target"
        target.write_text("foreign\n", encoding="utf-8")
        foreign = foreign_home / "aips"
        foreign.symlink_to(target)
        env_foreign = make_env(base / "foreign-runtime", base / "foreign-validation.log", bin_home=foreign_home)
        foreign_result = cli(system, ["install"], env_foreign)
        require(foreign_result.returncode != 0 and "not owned by this AIPS installation" in foreign_result.stderr, "Foreign symlink collision must stop install")
        require(foreign.is_symlink() and foreign.resolve() == target.resolve(), "Foreign symlink collision was replaced")

        owned_home = base / "owned-bin"
        owned_home.mkdir()
        owned = owned_home / "aips"
        owned.symlink_to(system / "bin" / "aips")
        env_owned = make_env(base / "owned-runtime", base / "owned-validation.log", bin_home=owned_home)
        owned_result = cli(system, ["install"], env_owned)
        require(owned_result.returncode == 0, f"Exact AIPS symlink should be reusable: {owned_result.stdout} {owned_result.stderr}")
        require(
            f'Until PATH is updated, run: "{owned}" doctor' in owned_result.stdout,
            "Install must print an absolute doctor command when AIPS_BIN_HOME is not on PATH",
        )
        require(
            f'Until PATH is updated, run: "{owned}" harness status' in owned_result.stdout,
            "Install must print an absolute Harness status command when AIPS_BIN_HOME is not on PATH",
        )
        require(owned.is_symlink() and owned.resolve() == (system / "bin" / "aips").resolve(), "Owned CLI symlink was not preserved")
        require((Path(env_owned["XDG_CONFIG_HOME"]) / "aips" / "system-dir").exists(), "Owned symlink reuse must record the installed system")
        require((Path(env_owned["XDG_CONFIG_HOME"]) / "aips" / "harness" / "installation.yaml").exists(), "Owned symlink reuse must continue through installation integrity and Harness registration")
        require(not (Path(env_owned["HOME"]) / ".zprofile").exists(), "Non-interactive install without --configure-shell must not modify a shell profile")


def shell_integration_lifecycle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, _ = system_fixture(base, "shell-integration")
        make_fake_venv(system)
        env = make_env(base / "runtime", base / "validation.log")
        env["SHELL"] = "/bin/zsh"
        env["PATH"] = f"{env['AIPS_BIN_HOME']}:{env['PATH']}"
        profile = Path(env["HOME"]) / ".zprofile"
        profile.write_text("# user setting\nexport USER_SETTING=preserved\n", encoding="utf-8")
        profile.chmod(0o640)

        configure_plan = run(["bash", str(system / "scripts" / "install.sh"), "--dry-run", "--configure-shell"], env=env)
        require(configure_plan.returncode == 0 and "shell_integration=configure" in configure_plan.stdout, "Download installer must accept and report --configure-shell")
        skip_plan = run(["bash", str(system / "scripts" / "install.sh"), "--dry-run", "--no-configure-shell"], env=env)
        require(skip_plan.returncode == 0 and "shell_integration=skip" in skip_plan.stdout, "Download installer must accept and report --no-configure-shell")

        installed = cli(system, ["install", "--configure-shell"], env)
        require(installed.returncode == 0, f"Managed shell install failed: {installed.stdout} {installed.stderr}")
        text = profile.read_text(encoding="utf-8")
        require(text.count("# >>> AIPS managed PATH >>>") == 1, "Managed shell block must be installed exactly once")
        require("Shell integration installed" in installed.stdout, "Explicit --configure-shell must persist integration even when the current process PATH already includes BIN_HOME")
        require("export USER_SETTING=preserved" in text, "Managed shell install must preserve user profile content")
        require(profile.stat().st_mode & 0o777 == 0o640, "Managed shell install must preserve profile permissions")
        status = cli(system, ["shell", "status"], env)
        require(status.returncode == 0 and "Shell integration: MANAGED" in status.stdout, "Shell status must report exact managed ownership")
        doctor = cli(system, ["doctor"], env)
        require("Shell integration: MANAGED" in doctor.stdout, "Doctor must report managed shell integration")
        require("CLI discoverability: OK" in doctor.stdout, "Doctor must report current-process CLI discoverability independently")

        repeated = cli(system, ["shell", "install"], env)
        require(repeated.returncode == 0, f"Repeated shell install failed: {repeated.stdout} {repeated.stderr}")
        require(profile.read_text(encoding="utf-8").count("# >>> AIPS managed PATH >>>") == 1, "Repeated shell install must be idempotent")

        bin_home = Path(env["AIPS_BIN_HOME"])
        other = bin_home / "other-tool"
        other.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        preserved = cli(system, ["uninstall"], env)
        require(preserved.returncode == 0, f"Default uninstall with shared bin failed: {preserved.stdout} {preserved.stderr}")
        require("Preserving shell PATH integration" in preserved.stderr, "Default uninstall must explain shared BIN_HOME preservation")
        require("# >>> AIPS managed PATH >>>" in profile.read_text(encoding="utf-8"), "Default uninstall must preserve PATH integration for a shared BIN_HOME")

        removed = cli(system, ["shell", "uninstall"], env)
        require(removed.returncode == 0, f"Explicit shell uninstall failed: {removed.stdout} {removed.stderr}")
        text = profile.read_text(encoding="utf-8")
        require("# >>> AIPS managed PATH >>>" not in text, "Explicit shell uninstall must remove the exact owned block")
        require("export USER_SETTING=preserved" in text, "Explicit shell uninstall must preserve user profile content")
        require(profile.stat().st_mode & 0o777 == 0o640, "Managed shell uninstall must preserve profile permissions")

        reinstalled = cli(system, ["shell", "install"], env)
        require(reinstalled.returncode == 0, "Shell integration reinstall must succeed")
        profile.write_text(profile.read_text(encoding="utf-8").replace("# Added by AIPS.", "# User changed AIPS block."), encoding="utf-8")
        conflict = cli(system, ["shell", "uninstall"], env)
        require(conflict.returncode != 0 and "modified; preserving it" in conflict.stderr, "Modified managed block must be preserved with a conflict")
        require("# User changed AIPS block." in profile.read_text(encoding="utf-8"), "Modified managed block was unexpectedly removed")

        duplicate_base = base / "duplicate"
        duplicate_env = make_env(duplicate_base, duplicate_base / "validation.log")
        duplicate_env["SHELL"] = "/bin/zsh"
        duplicate_profile = Path(duplicate_env["HOME"]) / ".zprofile"
        duplicate_install = cli(system, ["shell", "install"], duplicate_env)
        require(duplicate_install.returncode == 0, "Duplicate-block fixture install failed")
        block = duplicate_profile.read_text(encoding="utf-8")
        duplicate_profile.write_text(block + "\n" + block, encoding="utf-8")
        duplicate_remove = cli(system, ["shell", "uninstall"], duplicate_env)
        require(duplicate_remove.returncode != 0 and "Multiple AIPS shell blocks" in duplicate_remove.stderr, "Multiple managed blocks must require manual review")
        require(duplicate_profile.read_text(encoding="utf-8").count("# >>> AIPS managed PATH >>>") == 2, "Multiple managed blocks must be preserved")

        bash_base = base / "bash-profile"
        bash_env = make_env(bash_base, bash_base / "validation.log")
        bash_env["SHELL"] = "/bin/bash"
        bash_install = cli(system, ["shell", "install"], bash_env)
        require(bash_install.returncode == 0, f"bash shell integration failed: {bash_install.stdout} {bash_install.stderr}")
        bash_profile_name = ".bash_profile" if sys.platform == "darwin" else ".bashrc"
        require((Path(bash_env["HOME"]) / bash_profile_name).is_file(), "Shell integration must select the platform-appropriate bash profile")

        custom_base = base / "custom path"
        custom_env = make_env(custom_base, custom_base / "validation.log")
        custom_env["SHELL"] = "/bin/zsh"
        custom_profile = Path(custom_env["HOME"]) / ".zprofile"
        custom = cli(system, ["shell", "install"], custom_env)
        require(custom.returncode == 0, f"Custom path shell install failed: {custom.stdout} {custom.stderr}")
        profile_shell = shutil.which("zsh") or shutil.which("bash")
        require(profile_shell is not None, "A compatible shell is required to validate the managed profile block")
        shell_check = run(
            [profile_shell, "-c", f"source {str(custom_profile)!r}; case :$PATH: in *:\"$AIPS_BIN_HOME\":*) exit 0;; *) exit 1;; esac"],
            env=custom_env,
        )
        require(shell_check.returncode == 0, "Managed profile block must support spaces in AIPS_BIN_HOME")


def main() -> int:
    preflight_and_project_lifecycle()
    divergence_gate()
    major_version_gate()
    cli_collision_contract()
    runtime_dependency_health_contract()
    runtime_python_compatibility_contract()
    shell_integration_lifecycle()
    print("install_preflight_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
