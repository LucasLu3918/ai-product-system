#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = ROOT / "scripts/python_bootstrap_verify.py"


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
        "AIPS_CONSTRAINTS_FILE", "AIPS_VERIFICATION_MODULES",
        "python -m pip install", "scripts/python_bootstrap_verify.py", "python -m pip check",
    ):
        require(required_token in install["run"], f"bootstrap behavior is missing {required_token}")
    require("import yaml" not in install["run"], "bootstrap verification must not hard-code a dependency module")
    require(action["inputs"]["verification-modules"]["required"] is True,
            "each workflow must declare the imports that verify its dependency profile")

    valid = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT), "--modules", "json\npathlib"],
        capture_output=True, text=True, check=False,
    )
    require(valid.returncode == 0, f"declared standard-library imports should pass: {valid.stderr}")
    missing = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT), "--modules", "aips_missing_bootstrap_contract_module"],
        capture_output=True, text=True, check=False,
    )
    require(missing.returncode == 1 and "cannot import declared module" in missing.stderr,
            "a missing declared module must fail bootstrap verification")
    malformed = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT), "--modules", "json; exit 0"],
        capture_output=True, text=True, check=False,
    )
    require(malformed.returncode == 2 and "dotted Python identifiers" in malformed.stderr,
            "module declarations must reject shell-like input")

    pilots = (
        ".github/workflows/mcp-codex-interop.yml",
        ".github/workflows/repository-health.yml",
        ".github/workflows/maintenance-reliability.yml",
    )
    for relative in pilots:
        workflow = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
        uses = [step.get("uses") for job in workflow.get("jobs", {}).values() for step in job.get("steps", [])]
        require("./.github/actions/aips-python-bootstrap" in uses, f"{relative} must use the shared bootstrap")
        require(workflow.get("permissions", {}).get("contents") == "read", f"{relative} must remain read-only")
        bootstrap = next(step for job in workflow.get("jobs", {}).values() for step in job.get("steps", [])
                         if step.get("uses") == "./.github/actions/aips-python-bootstrap")
        modules = str((bootstrap.get("with") or {}).get("verification-modules") or "").split()
        require(modules == ["yaml"], f"{relative} must declare the imports used by its requirements profile")

    interop_text = (ROOT / pilots[0]).read_text(encoding="utf-8")
    require('".github/actions/aips-python-bootstrap/**"' in interop_text,
            "the pilot pull request filter must include shared action changes")

    health = yaml.safe_load((ROOT / ".github/workflows/repository-health.yml").read_text(encoding="utf-8"))
    require(health["jobs"]["observe"]["timeout-minutes"] == 10,
            "repository health must keep its evidence-backed provisional timeout")
    require(health["concurrency"]["cancel-in-progress"] is False,
            "repository health must preserve an in-progress report")
    require("${{ github.sha }}" in health["concurrency"]["group"],
            "repository health concurrency must distinguish exact revisions")

    maintenance = yaml.safe_load((ROOT / ".github/workflows/maintenance-reliability.yml").read_text(encoding="utf-8"))
    require(maintenance["concurrency"]["cancel-in-progress"] is False,
            "maintenance reliability must serialize cohort issue reconciliation without cancellation")
    require(maintenance["concurrency"]["queue"] == "max",
            "maintenance reliability must retain same-cohort pending reports instead of replacing them")
    require("inputs.period" in maintenance["concurrency"]["group"],
            "maintenance reliability concurrency must distinguish requested cohorts")
    report_steps = maintenance["jobs"]["report"]["steps"]
    require(any(step.get("uses") == "./.github/actions/aips-python-bootstrap" for step in report_steps),
            "maintenance reliability must use the shared Python bootstrap")
    require("timeout-minutes" not in maintenance["jobs"]["report"],
            "do not guess a maintenance timeout before a completed timing sample exists")

    collector = yaml.safe_load((ROOT / ".github/workflows/validation-observation-collector.yml").read_text(encoding="utf-8"))
    require(collector["jobs"]["collect"]["timeout-minutes"] == 15,
            "validation observation must retain its existing conservative timeout")
    require(any(step.get("uses") == "./.github/actions/aips-python-bootstrap"
                for step in collector["jobs"]["collect"]["steps"]),
            "validation observation must retain the shared Python bootstrap")

    effectiveness = yaml.safe_load((ROOT / ".github/workflows/evolution-effectiveness.yml").read_text(encoding="utf-8"))
    concurrency = effectiveness.get("concurrency") or {}
    require(concurrency.get("group") == "evolution-effectiveness-${{ github.repository }}-${{ github.event.inputs.period || 'scheduled' }}",
            "Evolution Effectiveness schedule and same-period dispatch must share a repository-scoped queue")
    require(concurrency.get("cancel-in-progress") is False,
            "Evolution Effectiveness must preserve in-progress Issue reconciliation")
    require(concurrency.get("queue") == "max",
            "Evolution Effectiveness must retain pending same-cohort Issue reconciliations")
    print("PASS: Python bootstrap, workflow execution profiles, and permission contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
