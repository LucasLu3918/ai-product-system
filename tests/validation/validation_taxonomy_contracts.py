"""Contracts for validation shadow/graduation taxonomy consistency."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validation_taxonomy.py"], cwd=ROOT,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "ALIGNED", report
    assert report["source_configs_modified"] is False
    assert report["selective_execution_enabled"] is False

    lifecycle = subprocess.run(
        [sys.executable, "tests/evidence/validation_taxonomy_lifecycle.py"], cwd=ROOT,
        capture_output=True, text=True, check=False,
    )
    assert lifecycle.returncode == 0, lifecycle.stderr + lifecycle.stdout


if __name__ == "__main__":
    run()
