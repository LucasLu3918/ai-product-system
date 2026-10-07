from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install.sh"


def invoke_process(arguments: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def git(root: Path, *args: str) -> None:
    result = invoke_process(["git", *args], cwd=root)
    if result.returncode:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")


def make_source(root: Path) -> None:
    (root / "bin").mkdir(parents=True)
    (root / "bin/aips").write_text(
        "#!/usr/bin/env bash\n"
        "test -d \"${AIPS_INSTALL_DIR}.aips-lock\" || exit 8\n"
        "printf 'CLI_INVOKED:%s\\n' \"$*\"\n",
        encoding="utf-8",
    )
    (root / "bin/aips").chmod(0o755)
    git(root, "init", "-q")
    git(root, "branch", "-M", "main")
    git(root, "config", "user.name", "AIPS Test")
    git(root, "config", "user.email", "aips-test" + chr(64) + "example.invalid")
    git(root, "add", "bin/aips")
    git(root, "commit", "-qm", "fixture")


def base_env(source: Path, install: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update({
        "AIPS_INSTALL_SOURCE": str(source),
        "AIPS_INSTALL_DIR": str(install),
        "AIPS_INSTALL_CHANNEL": "main",
        "AIPS_INSTALL_BRANCH": "main",
        "AIPS_REPO_URL": "https://example.invalid/aips.git",
        "HOME": str(install.parent / "home"),
        "XDG_DATA_HOME": str(install.parent / "data"),
    })
    return env


def successful_promotion(base: Path, source: Path) -> None:
    install = base / "data/aips/system"
    result = invoke_process(["bash", str(INSTALLER), "--no-configure-shell"], env=base_env(source, install))
    assert result.returncode == 0, f"install failed: {result.stdout} {result.stderr}"
    assert "CLI_INVOKED:install --no-configure-shell" in result.stdout
    assert (install / ".git").is_dir(), "verified staged clone was not promoted"
    assert not Path(f"{install}.aips-lock").exists(), "installer lock remained after success"
    assert not list(base.glob("data/aips/system.aips-stage.*")), "stage directory remained after promotion"


def lock_contention(base: Path, source: Path) -> None:
    install = base / "locked/aips/system"
    lock = Path(f"{install}.aips-lock")
    lock.mkdir(parents=True)
    (lock / "owner").write_text(f"pid={os.getpid()}\nhost={os.uname().nodename}\nstarted=1\n", encoding="utf-8")
    result = invoke_process(["bash", str(INSTALLER)], env=base_env(source, install))
    assert result.returncode != 0 and "installer lock exists" in result.stderr
    assert not install.exists(), "contended install modified its destination"
    assert lock.is_dir(), "active lock must not be removed by another installer"


def stale_lock_is_reported(base: Path, source: Path) -> None:
    install = base / "stale/aips/system"
    lock = Path(f"{install}.aips-lock")
    lock.mkdir(parents=True)
    (lock / "owner").write_text(f"pid=99999999\nhost={os.uname().nodename}\nstarted=1\n", encoding="utf-8")
    result = invoke_process(["bash", str(INSTALLER)], env=base_env(source, install))
    assert result.returncode != 0 and "stale" in result.stderr
    assert lock.is_dir(), "stale lock should require an explicit safe recovery step"


def failed_partial_clone_is_cleaned(base: Path, source: Path) -> None:
    install = base / "failed/aips/system"
    fake_bin = base / "fake-bin"
    fake_bin.mkdir()
    real_git = shutil.which("git")
    assert real_git
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/usr/bin/env bash\n"
        "if [ \"${1:-}\" = clone ]; then\n"
        "  for target in \"$@\"; do :; done\n"
        "  mkdir -p \"$target/.git\"\n"
        "  printf partial > \"$target/.git/partial\"\n"
        "  exit 1\n"
        "fi\n"
        "exec \"$REAL_GIT\" \"$@\"\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    env = base_env(source, install)
    env["REAL_GIT"] = real_git
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
    result = invoke_process(["bash", str(INSTALLER)], env=env)
    assert result.returncode != 0, "injected clone failure unexpectedly succeeded"
    assert not install.exists(), "partial clone became the active installation"
    assert not Path(f"{install}.aips-lock").exists(), "lock remained after clone failure"
    assert not list(base.glob("failed/aips/system.aips-stage.*")), "partial staging directory was not removed"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aips-installer-reliability-") as tmp:
        base = Path(tmp)
        source = base / "source"
        source.mkdir()
        make_source(source)
        successful_promotion(base, source)
        lock_contention(base, source)
        stale_lock_is_reported(base, source)
        failed_partial_clone_is_cleaned(base, source)
    print("installer reliability lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
