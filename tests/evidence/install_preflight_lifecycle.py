from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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
        ignore=shutil.ignore_patterns(".git", ".venv", ".venv.*", "node_modules", "__pycache__", "*.pyc"),
    )
    sentinel_validator(system)
    git(system, "init", "-q")
    git(system, "branch", "-m", "main")
    configure_git(system)
    git(system, "add", "-A")
    git(system, "commit", "-qm", "fixture baseline")
    run(["git", "clone", "--no-local", "--bare", str(system), str(remote)], check=True)
    git(system, "remote", "add", "origin", str(remote))
    return system, remote


def remote_commit(remote: Path, base: Path, name: str, mutate) -> str:
    updater = base / name
    run(["git", "clone", "--no-local", "-q", str(remote), str(updater)], check=True)
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
    nested_project = project / "nested"
    nested_project.mkdir()
    (nested_project / "app.txt").write_text("nested product\n", encoding="utf-8")
    git(project, "init", "-q")
    git(project, "branch", "-m", "main")
    configure_git(project)
    git(project, "add", "app.txt", "nested/app.txt")
    git(project, "commit", "-qm", "product baseline")
    baseline = git(project, "rev-parse", "HEAD").stdout.strip()
    run(["git", "clone", "--no-local", "--bare", str(project), str(remote)], check=True)
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
        require(dirty_result.returncode == 0 and "skipping the automatic update" in dirty_result.stderr,
                "Preflight must skip the update and continue for dirty system worktree: "
                + dirty_result.stdout + dirty_result.stderr)
        require(dirty.exists() and dirty.read_text(encoding="utf-8") == "dirty\n", "Degraded preflight must keep local changes")
        dirty.unlink()

        project_check = cli(system, ["project", "check", str(project)], env)
        require(project_check.returncode == 0, f"project check failed for valid EPHEMERAL project: {project_check.stdout} {project_check.stderr}")
        require("Project mode: EXTERNAL" in project_check.stdout, "project check must report external state")
        require("Project Intelligence freshness:" in project_check.stdout, "project check must report freshness or UNKNOWN")
        require(not (project / ".ai").exists(), "project check must not create a workspace")
        invalid_project_check = cli(system, ["project", "check", str(base / "missing-project")], env)
        require(invalid_project_check.returncode != 0, "project check must reject a missing project path")

        first = cli(system, ["preflight", str(project)], env)
        require(first.returncode == 0, f"clean main preflight failed: {first.stdout} {first.stderr}")
        require("Project mode: EXTERNAL" in first.stdout, "Preflight must report external state without .ai")
        require(not (project / ".ai").exists(), "Preflight must not auto-attach an EPHEMERAL project")
        require(not (system / ".venv").exists(), "Plain source preflight must not create a managed virtual environment")
        require(marker.exists(), "Preflight must validate the system")
        require(git(project, "rev-parse", "HEAD").stdout.strip() == product_head, "Preflight must not pull target product repository")
        require((project / "app.txt").read_text(encoding="utf-8") == product_text, "Preflight changed target product source")

        canonical_preflight = cli(system, ["system", "preflight", str(project)], env)
        require(canonical_preflight.returncode == 0, f"system preflight alias failed: {canonical_preflight.stdout} {canonical_preflight.stderr}")
        require("Update Preflight passed." in canonical_preflight.stdout, "system preflight must delegate to the existing preflight lifecycle")

        exclude_file = Path(git(project, "rev-parse", "--git-path", "info/exclude").stdout.strip())
        if not exclude_file.is_absolute():
            exclude_file = project / exclude_file
        exclude_file.parent.mkdir(parents=True, exist_ok=True)
        exclude_file.write_text("# preserve this local rule\nkeep-local-data.tmp\n", encoding="utf-8")
        exclude_before = exclude_file.read_bytes()
        gitignore_before = (project / ".gitignore").read_bytes() if (project / ".gitignore").exists() else None

        attached = cli(system, ["attach", str(project)], env)
        require(attached.returncode == 0 and not (project / ".ai").exists(), f"attach must use external state: {attached.stdout} {attached.stderr}")
        require(exclude_file.read_bytes() == exclude_before, "Attach must not change Git info/exclude")
        require((project / ".gitignore").read_bytes() == gitignore_before if gitignore_before is not None else not (project / ".gitignore").exists(),
                "Attach must not create or modify the project .gitignore")
        require(not git(project, "status", "--short", check=False).stdout.strip(), "External AIPS state must not appear in Git status after attach")

        repeated_attach = cli(system, ["attach", str(project)], env)
        require(repeated_attach.returncode == 0, f"repeated attach failed: {repeated_attach.stdout} {repeated_attach.stderr}")
        require(exclude_file.read_bytes() == exclude_before and not (project / ".ai").exists(),
                "Repeated attach must leave the repository unchanged")

        nested_project = project / "nested"
        nested_attached = cli(system, ["attach", str(nested_project)], env)
        require(nested_attached.returncode == 0 and not (nested_project / ".ai").exists(),
                f"attach to a nested project failed: {nested_attached.stdout} {nested_attached.stderr}")
        require(exclude_file.read_bytes() == exclude_before, "Nested attach must not change parent Git excludes")

        non_git_project = base / "non-git-project"
        non_git_project.mkdir()
        non_git_attach = cli(system, ["attach", str(non_git_project)], env)
        require(non_git_attach.returncode == 0 and not (non_git_project / ".ai").exists(),
                f"attach to a non-Git project failed: {non_git_attach.stdout} {non_git_attach.stderr}")
        require(not (non_git_project / ".git").exists() and not (non_git_project / ".gitignore").exists(),
                "Non-Git attach must not create Git metadata")

        status = cli(system, ["status", str(project)], env)
        require(status.returncode == 0 and "Project mode: EXTERNAL" in status.stdout and "External Project Intelligence: resolvable" in status.stdout,
                "status must report external project state")
        attached_check = cli(system, ["project", "check", str(project)], env)
        require(attached_check.returncode == 0 and "Project mode: EXTERNAL" in attached_check.stdout, "project check must report external mode")

        old_version = (system / "VERSION").read_text(encoding="utf-8").strip()
        upgraded_version = next_patch(old_version)

        def system_update(updater: Path) -> None:
            (updater / "VERSION").write_text(upgraded_version + "\n", encoding="utf-8")
            cli_path = updater / "scripts" / "aips_cli" / "maintenance.sh"
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
        require(not (project / ".ai").exists(), "Preflight must not write AIPS provenance into the project")
        require(git(project, "rev-parse", "HEAD").stdout.strip() == product_head, "Preflight pulled target product repository")

        detached = cli(system, ["detach", str(project)], env)
        require(detached.returncode == 0 and not (project / ".ai").exists(), f"detach failed: {detached.stdout} {detached.stderr}")
        require(not list(project.glob(".ai.detached-*")), "Detach must not create project-local archives")
        require(exclude_file.read_bytes() == exclude_before, "Detach must not change Git info/exclude")
        require((project / "app.txt").read_text(encoding="utf-8") == product_text, "Detach modified product source")

        restored = cli(system, ["attach", str(project)], env)
        require(restored.returncode == 0 and not (project / ".ai").exists(), "Repeated external attach must remain repository-independent")

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
        legacy_project_state = project / ".ai"
        legacy_project_state.mkdir(parents=True, exist_ok=True)
        legacy_sentinel = legacy_project_state / "legacy-user-data.txt"
        legacy_sentinel.write_text("preserve legacy project data\n", encoding="utf-8")
        venv = system / ".venv"
        venv.mkdir()
        (venv / "preserve.txt").write_text("preserve\n", encoding="utf-8")

        uninstalled = cli(system, ["uninstall"], env)
        require(uninstalled.returncode == 0, f"default uninstall failed: {uninstalled.stdout} {uninstalled.stderr}")
        require(not cli_link.exists(), "Default uninstall must remove AIPS-owned CLI symlink")
        require(legacy_sentinel.read_text(encoding="utf-8") == "preserve legacy project data\n",
                "Default uninstall must preserve existing project .ai user data")
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
        installed_sha = git(system, "rev-parse", "HEAD").stdout.strip()
        installed_version = (system / "VERSION").read_text(encoding="utf-8")
        result = cli(system, ["preflight", str(project)], env)
        require(result.returncode != 0 and "diverged" in result.stderr, "Preflight must never auto merge/rebase divergent system history")
        require(git(system, "rev-parse", "HEAD").stdout.strip() == installed_sha,
                "Rejected divergent update must leave the installed system commit unchanged")
        require((system / "VERSION").read_text(encoding="utf-8") == installed_version,
                "Rejected divergent update must leave the installed system version unchanged")


def stable_update_without_tag_gate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, _ = system_fixture(base, "stable-without-tag")
        env = make_env(base / "runtime", base / "validation.log")
        channel_path = Path(git(system, "rev-parse", "--path-format=absolute", "--git-path", "aips-channel").stdout.strip())
        channel_path.write_text("stable\n", encoding="utf-8")
        installed_sha = git(system, "rev-parse", "HEAD").stdout.strip()
        installed_version = (system / "VERSION").read_text(encoding="utf-8")

        result = cli(system, ["update"], env)
        require(result.returncode != 0 and "No stable release tag exists yet" in result.stderr,
                "Stable updater must fail closed when the remote has no verified release tag")
        require(git(system, "rev-parse", "HEAD").stdout.strip() == installed_sha,
                "Stable update without a release tag must leave the installed commit unchanged")
        require((system / "VERSION").read_text(encoding="utf-8") == installed_version,
                "Stable update without a release tag must leave the installed version unchanged")


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
    body = f"""#!{sys.executable}
import os
import sys
if len(sys.argv) >= 3 and sys.argv[1] == "-c" and "sys.version_info" in sys.argv[2]:
    raise SystemExit(1)
if len(sys.argv) >= 2 and sys.argv[1] == "--version":
    print("Python 3.11.13")
    raise SystemExit(0)
if len(sys.argv) >= 3 and sys.argv[1] == "-c" and "import yaml, mcp" in sys.argv[2]:
    raise SystemExit(0)
os.execv({sys.executable!r}, [{sys.executable!r}] + sys.argv[1:])
"""
    py.write_text(body, encoding="utf-8")
    py.chmod(0o755)


def make_fake_python_creator(base: Path, marker: Path, version: tuple[int, int] = (3, 12)) -> Path:
    creator = base / "python3-compatible"
    runtime_body = f"""#!{sys.executable}
import os
from pathlib import Path
import sys
marker = Path({str(marker)!r})
if len(sys.argv) >= 3 and sys.argv[1:3] == ["-m", "pip"]:
    marker.write_text("installed\\n", encoding="utf-8")
    raise SystemExit(0)
if len(sys.argv) >= 3 and sys.argv[1] == "-c" and "sys.version_info" in sys.argv[2]:
    raise SystemExit(0 if {version!r} >= (3, 12) else 1)
if len(sys.argv) >= 3 and sys.argv[1] == "-c" and "import yaml, mcp" in sys.argv[2]:
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
    raise SystemExit(0 if {version!r} >= (3, 12) else 1)
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

        unsupported_doctor = cli(system, ["doctor"], env)
        require("runtime Python: UNSUPPORTED" in unsupported_doctor.stderr, "Doctor must explain when the managed runtime is below Python 3.12")

        repaired = cli(system, ["update"], env)
        require(repaired.returncode == 0, f"Unsupported managed Python repair failed: {repaired.stdout} {repaired.stderr}")
        require("unsupported Python" in repaired.stdout + repaired.stderr, f"Repair must explain why the managed virtual environment is recreated: {repaired.stdout} {repaired.stderr}")
        require(dependency_marker.exists(), "Recreated managed virtual environment must install runtime dependencies")
        venv = system / ".venv" / "bin" / "python"
        require(venv.exists(), "Recreated managed virtual environment Python is missing")


def explicit_unsupported_python_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system, _ = system_fixture(base, "unsupported-explicit-python")
        creator = make_fake_python_creator(base, base / "dependencies-installed", version=(3, 11))
        env = make_env(base / "runtime", base / "validation.log")
        env["AIPS_PYTHON"] = str(creator)
        blocked = cli(system, ["install"], env)
        require(blocked.returncode != 0, "Explicit Python 3.11 must not install AIPS after the supported floor is raised")
        require("AIPS requires Python 3.12 or newer" in blocked.stderr, "Unsupported explicit Python must have a migration diagnostic")
        require(not (system / ".venv").exists(), "Unsupported explicit Python must fail before creating a partial managed venv")


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

        marker_env = make_env(base / "marker-runtime", base / "marker-validation.log")
        marker_dir = Path(marker_env["XDG_CONFIG_HOME"]) / "aips"
        marker_dir.mkdir(parents=True)
        foreign_data = base / "foreign-marker-target"
        foreign_data.write_text("preserve user data\n", encoding="utf-8")
        marker_path = marker_dir / "system-dir"
        marker_path.symlink_to(foreign_data)
        marker_result = cli(system, ["install"], marker_env)
        require(marker_result.returncode != 0, "system-dir symlink must stop install")
        require(foreign_data.read_text(encoding="utf-8") == "preserve user data\n", "system-dir symlink target was overwritten")
        require(not (Path(marker_env["AIPS_BIN_HOME"]) / "aips").exists(), "marker conflict must not create a CLI link")
        marker_path.unlink()
        marker_path.write_text("/different/system\n", encoding="utf-8")
        foreign_marker = cli(system, ["install"], marker_env)
        require(foreign_marker.returncode != 0, "foreign system marker must stop install")
        require(marker_path.read_text(encoding="utf-8") == "/different/system\n", "foreign system marker was overwritten")

        alias = base / "system-alias"
        alias.symlink_to(system, target_is_directory=True)
        alias_marker = str(alias) + "\n"
        marker_path.write_text(alias_marker, encoding="utf-8")
        alias_install = cli(system, ["install"], marker_env)
        require(alias_install.returncode == 0, f"equivalent system marker should be accepted: {alias_install.stderr}")
        require(marker_path.read_text(encoding="utf-8") == alias_marker, "equivalent existing marker must not be rewritten")

        linkfail_env = make_env(base / "linkfail-runtime", base / "linkfail-validation.log")
        fake_link = base / "linkfail-runtime" / "fake-bin" / "ln"
        fake_link.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        fake_link.chmod(0o755)
        link_failure = cli(system, ["install"], linkfail_env)
        require(link_failure.returncode != 0, "install must not report success when CLI link creation fails")
        require(not (Path(linkfail_env["AIPS_BIN_HOME"]) / "aips").exists(), "failed link fixture unexpectedly created CLI link")

        owned_home = base / "owned-bin"
        owned_home.mkdir()
        owned = owned_home / "aips"
        owned.symlink_to(system / "bin" / "aips")
        env_owned = make_env(base / "owned-runtime", base / "owned-validation.log", bin_home=owned_home)
        host_settings = Path(env_owned["HOME"]) / ".claude" / "settings.json"
        host_settings.parent.mkdir(parents=True)
        host_original = b'{ "keep" : true, "hooks": {} }\n'
        host_settings.write_bytes(host_original)
        previous_umask = os.umask(0o002)
        try:
            owned_result = cli(system, ["install"], env_owned)
        finally:
            os.umask(previous_umask)
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
        system_marker = Path(env_owned["XDG_CONFIG_HOME"]) / "aips" / "system-dir"
        require(system_marker.exists(), "Owned symlink reuse must record the installed system")
        require(system_marker.stat().st_mode & 0o077 == 0, "new system marker must remain private under a permissive umask")
        harness_manifest = Path(env_owned["XDG_CONFIG_HOME"]) / "aips" / "harness" / "installation.yaml"
        require(not harness_manifest.exists(), "fresh install must not implicitly enable Harness")
        off_status = cli(system, ["harness", "status"], env_owned)
        require(off_status.returncode == 0 and "Harness: OFF" in off_status.stdout, "status must report Harness OFF")
        off_doctor = cli(system, ["harness", "doctor"], env_owned)
        require(off_doctor.returncode == 0 and "Harness: OFF" in off_doctor.stdout, "doctor must accept intentionally disabled Harness")
        off_refresh = cli(system, ["_refresh-harness-after-update"], env_owned)
        require(off_refresh.returncode == 0 and not harness_manifest.exists(), "update must not implicitly enable Harness")
        project = base / "off-project"
        project.mkdir()
        update = cli(system, ["update"], env_owned)
        require(update.returncode == 0 and not harness_manifest.exists(), f"update enabled Harness: {update.stderr}")
        preflight = cli(system, ["preflight", str(project)], env_owned)
        require(preflight.returncode == 0 and not harness_manifest.exists(), f"preflight enabled Harness: {preflight.stderr}")
        require(host_settings.read_bytes() == host_original, "off install/update/preflight modified host settings")
        require(not (project / ".ai").exists(), "off preflight modified project state")
        previous_umask = os.umask(0o002)
        try:
            explicit = cli(system, ["harness", "install"], env_owned)
        finally:
            os.umask(previous_umask)
        require(explicit.returncode == 0 and harness_manifest.exists(), "explicit Harness installation must register ownership")
        require(harness_manifest.parent.stat().st_mode & 0o022 == 0, "new Harness state must not be group- or world-writable")
        enabled_refresh = cli(system, ["_refresh-harness-after-update"], env_owned)
        require(enabled_refresh.returncode == 0 and "Refreshing AIPS Global Harness" in enabled_refresh.stdout, "explicitly enabled Harness must continue to refresh")
        harness_manifest.write_text("bad: [", encoding="utf-8")
        unknown_refresh = cli(system, ["_refresh-harness-after-update"], env_owned)
        require(unknown_refresh.returncode == 0, "unknown enablement must not stop ordinary update")
        require("Harness enablement is unknown" in unknown_refresh.stderr, "unknown enablement must be reported")
        require(harness_manifest.read_text(encoding="utf-8") == "bad: [", "unknown ownership must be preserved")
        unknown_status = cli(system, ["harness", "status"], env_owned)
        require("Harness: UNKNOWN" in unknown_status.stdout, "status must not report invalid ownership as active")
        unknown_doctor = cli(system, ["harness", "doctor"], env_owned)
        require(unknown_doctor.returncode != 0 and "UNKNOWN" in unknown_doctor.stderr, "doctor must report invalid ownership")
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



def uninstall_without_harness_preserves_host_settings() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system = base / "uninstall-no-harness-system"
        shutil.copytree(
            ROOT, system,
            ignore=shutil.ignore_patterns(".git", ".venv", ".venv.*", "node_modules", "__pycache__", "*.pyc"),
        )
        make_fake_venv(system)
        env = make_env(base / "runtime", base / "validation.log")
        settings = Path(env["HOME"]) / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True)
        original = b'{ "user-setting" : true, "hooks": {} }\n'
        settings.write_bytes(original)
        harness = Path(env["XDG_CONFIG_HOME"]) / "aips" / "harness"
        require(not harness.exists(), "fixture must not have harness state")
        result = cli(system, ["uninstall"], env)
        require(result.returncode == 0, f"uninstall without harness failed: {result.stdout} {result.stderr}")
        require(settings.read_bytes() == original, "uninstall without harness changed unowned host settings")
        require(not harness.exists(), "uninstall must not create harness state")
        direct = cli(system, ["harness", "uninstall"], env)
        require(direct.returncode == 0, f"direct uninstall without harness failed: {direct.stderr}")
        require(settings.read_bytes() == original, "direct uninstall without harness changed host settings")



def uninstall_with_partial_harness_preserves_user_data() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        system = base / "uninstall-partial-harness-system"
        shutil.copytree(
            ROOT, system,
            ignore=shutil.ignore_patterns(".git", ".venv", ".venv.*", "node_modules", "__pycache__", "*.pyc"),
        )
        make_fake_venv(system)
        env = make_env(base / "runtime", base / "validation.log")
        harness = Path(env["XDG_CONFIG_HOME"]) / "aips" / "harness"
        harness.mkdir(parents=True)
        note = harness / "user-note.txt"
        note.write_text("preserve user data\n", encoding="utf-8")
        settings = Path(env["HOME"]) / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True)
        original = b'{ "user-setting" : true, "hooks": {} }\n'
        settings.write_bytes(original)
        result = cli(system, ["uninstall"], env)
        require(result.returncode != 0, "ambiguous harness ownership must stop uninstall")
        require(note.read_text(encoding="utf-8") == "preserve user data\n", "partial harness state was removed")
        require(settings.read_bytes() == original, "ambiguous harness uninstall changed host settings")
        require("harness doctor" in result.stderr, "partial state must report recovery guidance")
        direct = cli(system, ["harness", "uninstall"], env)
        require(direct.returncode != 0, "direct uninstall must refuse ambiguous harness ownership")
        require(note.exists() and settings.read_bytes() == original, "direct uninstall changed ambiguous state")

        owned_env = make_env(base / "owned-runtime", base / "owned-validation.log")
        owned_system = base / "owned-harness-system"
        shutil.copytree(
            ROOT, owned_system,
            ignore=shutil.ignore_patterns(".git", ".venv", ".venv.*", "node_modules", "__pycache__", "*.pyc"),
        )
        make_fake_venv(owned_system)
        installed = cli(owned_system, ["harness", "install"], owned_env)
        require(installed.returncode == 0, f"explicit Harness install failed: {installed.stdout} {installed.stderr}")
        owned_harness = Path(owned_env["XDG_CONFIG_HOME"]) / "aips" / "harness"
        retained = owned_harness / "user-note.txt"
        retained.write_text("preserve after owned uninstall\n", encoding="utf-8")
        removed = cli(owned_system, ["harness", "uninstall"], owned_env)
        require(removed.returncode == 0, f"owned Harness uninstall failed: {removed.stdout} {removed.stderr}")
        require(retained.read_text(encoding="utf-8") == "preserve after owned uninstall\n", "uninstall deleted unrecognized user data")
        disabled = cli(owned_system, ["harness", "status"], owned_env)
        require(disabled.returncode == 0 and "Harness: OFF" in disabled.stdout, "uninstalled Harness state must report OFF")
        require("AUTOMATIC" not in disabled.stdout, "OFF status must not expose stale adapter state as active")
        repeated = cli(owned_system, ["harness", "uninstall"], owned_env)
        require(repeated.returncode == 0 and "already OFF" in repeated.stdout, "repeated uninstall must be safe and idempotent")
        refresh = cli(owned_system, ["_refresh-harness-after-update"], owned_env)
        require(refresh.returncode == 0, f"ordinary refresh failed after uninstall: {refresh.stderr}")
        require("Harness: OFF" in cli(owned_system, ["harness", "status"], owned_env).stdout, "refresh re-enabled explicitly uninstalled Harness")

        outside = base / "unowned-manifest.yaml"
        outside.write_text("user-owned manifest\n", encoding="utf-8")
        (harness / "installation.yaml").symlink_to(outside)
        linked = cli(system, ["uninstall"], env)
        require(linked.returncode != 0, "symlinked ownership must stop uninstall")
        require(outside.read_text(encoding="utf-8") == "user-owned manifest\n", "symlink target was modified")
        require(note.exists() and settings.read_bytes() == original, "symlinked ownership must preserve state")
        direct_linked = cli(system, ["harness", "uninstall"], env)
        require(direct_linked.returncode != 0 and note.exists(), "direct uninstall must preserve symlinked ownership state")

        link_env = make_env(base / "link-runtime", base / "link-validation.log")
        config = Path(link_env["XDG_CONFIG_HOME"]) / "aips"
        config.mkdir(parents=True)
        target = base / "unowned-directory"
        target.mkdir()
        (target / "note.txt").write_text("preserve\n", encoding="utf-8")
        (config / "harness").symlink_to(target, target_is_directory=True)
        linked_dir = cli(system, ["uninstall"], link_env)
        require(linked_dir.returncode != 0, "symlinked harness directory must stop uninstall")
        require((target / "note.txt").read_text(encoding="utf-8") == "preserve\n", "symlinked directory target was modified")
        direct_dir = cli(system, ["harness", "uninstall"], link_env)
        require(direct_dir.returncode != 0 and (target / "note.txt").exists(), "direct uninstall must preserve symlinked directory")


def main() -> int:
    uninstall_without_harness_preserves_host_settings()
    uninstall_with_partial_harness_preserves_user_data()
    preflight_and_project_lifecycle()
    divergence_gate()
    stable_update_without_tag_gate()
    major_version_gate()
    cli_collision_contract()
    runtime_dependency_health_contract()
    runtime_python_compatibility_contract()
    explicit_unsupported_python_contract()
    shell_integration_lifecycle()
    print("install_preflight_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
