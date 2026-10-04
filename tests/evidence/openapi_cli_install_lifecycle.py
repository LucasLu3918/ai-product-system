#!/usr/bin/env python3
"""Exercise optional OpenAPI installation and the installed product CLI boundary."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(system: Path, args: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(system / "bin" / "aips"), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aips openapi install ") as temporary:
        base = Path(temporary)
        system = base / "installed AIPS"
        (system / "bin").mkdir(parents=True)
        (system / "scripts").mkdir()
        (system / ".venv" / "bin").mkdir(parents=True)
        shutil.copy2(ROOT / "bin" / "aips", system / "bin" / "aips")
        shutil.copy2(ROOT / "requirements-openapi.txt", system / "requirements-openapi.txt")

        marker = base / "optional-dependencies-installed"
        fake_python = system / ".venv" / "bin" / "python"
        fake_python.write_text(
            f"""#!{sys.executable}
from pathlib import Path
import os
import sys
marker = Path({str(marker)!r})
if sys.argv[1:3] == ["-m", "pip"]:
    expected = str(Path(__file__).resolve().parents[2] / "requirements-openapi.txt")
    if "-r" not in sys.argv or sys.argv[sys.argv.index("-r") + 1] != expected:
        raise SystemExit(7)
    marker.write_text("installed\\n", encoding="utf-8")
    raise SystemExit(0)
if len(sys.argv) >= 3 and sys.argv[1] == "-c":
    code = sys.argv[2]
    if "import yaml" in code:
        raise SystemExit(0)
    if "import openapi_spec_validator, jsonschema" in code:
        raise SystemExit(0 if marker.exists() else 1)
    if "sys.version_info" in code:
        raise SystemExit(0)
os.execv({sys.executable!r}, [{sys.executable!r}] + sys.argv[1:])
""",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        (system / "scripts" / "openapi_contracts.py").write_text(
            "import json, os, sys\nprint(json.dumps({'cwd': os.getcwd(), 'argv': sys.argv[1:]}))\n",
            encoding="utf-8",
        )

        product = base / "independent product"
        product.mkdir()
        (product / "openapi.yaml").write_text(
            "openapi: 3.0.3\ninfo: {title: Independent fixture, version: '1'}\npaths: {}\n",
            encoding="utf-8",
        )
        env = dict(os.environ)
        env.update({"HOME": str(base / "home"), "XDG_CONFIG_HOME": str(base / "config")})
        env.pop("AIPS_VALIDATION_PYTHON", None)
        env.pop("AIPS_VALIDATION_VENV", None)
        (base / "home").mkdir()

        initial = run(system, ["openapi", "doctor"], cwd=product, env=env)
        assert initial.returncode == 0 and "NOT_INSTALLED" in initial.stdout, initial.stdout + initial.stderr

        missing = run(
            system,
            ["openapi", "validate", "openapi.yaml", "--repo-root", str(product)],
            cwd=product,
            env=env,
        )
        assert missing.returncode != 0, "contract command must stop before invoking the validator without optional packages"
        assert "aips openapi install" in missing.stderr and "Traceback" not in missing.stderr, missing.stderr

        installed = run(system, ["openapi", "install"], cwd=product, env=env)
        assert installed.returncode == 0 and marker.exists(), installed.stdout + installed.stderr
        assert str(system / "requirements-openapi.txt") in installed.stdout or "installed in" in installed.stdout

        ready = run(system, ["openapi", "doctor"], cwd=product, env=env)
        assert ready.returncode == 0 and "READY" in ready.stdout, ready.stdout + ready.stderr

        validation = run(
            system,
            ["openapi", "validate", "openapi.yaml", "--repo-root", str(product)],
            cwd=product,
            env=env,
        )
        assert validation.returncode == 0, validation.stdout + validation.stderr
        result = json.loads(validation.stdout)
        assert Path(result["cwd"]).resolve() == product.resolve(), result
        assert result["argv"][:3] == ["validate", "openapi.yaml", "--repo-root"], result
        assert Path(result["argv"][3]).resolve() == product.resolve(), result

    print("openapi_cli_install_lifecycle evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
