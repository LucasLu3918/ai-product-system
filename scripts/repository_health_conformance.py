from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def run_scenario_conformance(
    root: Path,
    helper: Path,
    registry: Path,
    scenario_dir: Path,
) -> list[str]:
    if not helper.exists():
        return [f"scenario helper missing: {relative_path(root, helper)}"]
    result = subprocess.run(
        [
            sys.executable,
            str(helper),
            "check",
            "--registry",
            str(registry),
            "--scenario-dir",
            str(scenario_dir),
            "--format",
            "json",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(result.stdout)
        problems = payload.get("errors") or []
        if result.returncode == 0 and payload.get("status") == "PASS":
            return []
        if problems:
            return [str(item) for item in problems]
    except json.JSONDecodeError:
        pass
    detail = (result.stdout + "\n" + result.stderr).strip()
    return [f"scenario conformance failed: {detail[:1200]}"]
