#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    action_path = ROOT / ".github/actions/aips-python-bootstrap/action.yml"
    action = yaml.safe_load(action_path.read_text(encoding="utf-8"))
    require(action["runs"]["using"] == "composite", "bootstrap must remain a composite action")
    steps = action["runs"]["steps"]
    setup = steps[0]
    require(setup["uses"].startswith("actions/setup-python@"), "Python setup action must be pinned")
    action_text = action_path.read_text(encoding="utf-8")
    require("# v" in action_text.split(setup["uses"], 1)[1].splitlines()[0],
            "Python setup action pin must state its reviewed version")
    require(setup["with"]["cache"] == "pip", "pip cache must remain enabled")
    install = steps[1]
    require(install["shell"] == "bash", "requirements parsing must use an explicit shell")
    for required_token in (
        "AIPS_REQUIREMENTS_FILES", "requirement_args+=(-r \"$file\")",
        "AIPS_CONSTRAINTS_FILE", "python -m pip install", "import yaml",
    ):
        require(required_token in install["run"], f"bootstrap behavior is missing {required_token}")

    pilots = (
        ".github/workflows/mcp-codex-interop.yml",
        ".github/workflows/repository-health.yml",
    )
    for relative in pilots:
        workflow = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
        uses = [step.get("uses") for job in workflow.get("jobs", {}).values() for step in job.get("steps", [])]
        require("./.github/actions/aips-python-bootstrap" in uses, f"{relative} must use the shared bootstrap")
        require(workflow.get("permissions", {}).get("contents") == "read", f"{relative} must remain read-only")

    interop_text = (ROOT / pilots[0]).read_text(encoding="utf-8")
    require('".github/actions/aips-python-bootstrap/**"' in interop_text,
            "the pilot pull request filter must include shared action changes")
    print("PASS: Python bootstrap action, pilot workflows, and read-only contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
