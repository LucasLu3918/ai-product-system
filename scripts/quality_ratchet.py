"""Enforce the existing Ruff debt ceiling without imposing a new target."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check",))
    parser.add_argument("--config", type=Path, default=ROOT / "config/quality-ratchet.yaml")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    baseline = int((config.get("ruff") or {}).get("baseline_findings", -1))
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--no-cache", "--output-format=json", "scripts", "tests"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        print(result.stderr.strip() or "Ruff could not produce a debt report", file=sys.stderr)
        return 2
    try:
        findings = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Ruff returned invalid JSON", file=sys.stderr)
        return 2
    count = len(findings)
    print(f"Ruff findings: {count}; allowed baseline: {baseline}")
    if count > baseline:
        print("QUALITY_RATCHET_BLOCKED: Ruff findings increased beyond the established baseline", file=sys.stderr)
        return 1
    mypy = config.get("mypy") or {}
    modules = [str(path) for path in mypy.get("modules") or []]
    with tempfile.TemporaryDirectory(prefix="aips-quality-mypy-") as cache_dir:
        type_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--cache-dir",
                cache_dir,
                "--follow-imports",
                str(mypy.get("follow_imports", "skip")),
                "--ignore-missing-imports",
                *modules,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    type_errors = sum(": error:" in line for line in type_result.stdout.splitlines())
    print(f"Mypy findings: {type_errors}; allowed baseline: {mypy.get('maximum_findings')}")
    if type_result.returncode not in (0, 1) or type_errors > int(mypy.get("maximum_findings", -1)):
        print(type_result.stdout.strip() or type_result.stderr.strip(), file=sys.stderr)
        print("QUALITY_RATCHET_BLOCKED: selected-module mypy debt increased", file=sys.stderr)
        return 1
    print("QUALITY_RATCHET_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
