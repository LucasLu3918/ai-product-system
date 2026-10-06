"""Verify the AIPS CLI facade loads its modules from the resolved checkout."""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULES = (
    "help.sh",
    "runtime.sh",
    "harness.sh",
    "commands.sh",
    "project.sh",
    "shell.sh",
    "installation.sh",
    "maintenance.sh",
    "dispatch.sh",
)


def run(entry: Path, args: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(entry), *args], cwd=cwd, env=env,
        capture_output=True, text=True, check=False,
    )


def main() -> int:
    facade = ROOT / "scripts" / "aips_cli.sh"
    source = facade.read_text(encoding="utf-8")
    for module in MODULES:
        require = f'source "$SCRIPT_DIR/aips_cli/{module}"'
        assert require in source, f"facade does not load {module} relative to its resolved checkout"
        assert (ROOT / "scripts" / "aips_cli" / module).is_file(), f"missing module: {module}"

    with tempfile.TemporaryDirectory(prefix="aips-cli-modules-") as temporary:
        base = Path(temporary)
        cwd = base / "unrelated-working-directory"
        home = base / "home"
        cwd.mkdir()
        home.mkdir()
        env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"))
        link = base / "aips"
        link.symlink_to(ROOT / "bin" / "aips")
        for entry in (ROOT / "bin" / "aips", link, facade):
            result = run(entry, ["help"], cwd, env)
            assert result.returncode == 0, result.stdout + result.stderr
            assert "Usage:" in result.stdout and "aips install" in result.stdout
            assert result.stderr == ""
        unknown = run(link, ["plan16-test-unknown"], cwd, env)
        assert unknown.returncode != 0
        assert "ERROR: Unknown command: plan16-test-unknown." in unknown.stderr
        assert "scripts/aips_cli.sh" not in unknown.stderr

    print("AIPS CLI MODULE EXTRACTION LIFECYCLE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
