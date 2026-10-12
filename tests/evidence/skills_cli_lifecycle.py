"""Exercise the public Skill list CLI from outside the AIPS checkout."""

from __future__ import annotations

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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["AIPS_VALIDATION_PYTHON"] = sys.executable
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

        require((ROOT / "skills/INDEX.yaml").read_bytes() == before,
                "listing Skills must not modify the generated index")

    print("Skill CLI lifecycle PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
