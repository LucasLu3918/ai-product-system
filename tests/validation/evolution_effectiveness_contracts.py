from pathlib import Path
import subprocess
import sys
import yaml

from .static_contracts import ROOT, errors

required = (
    ROOT / "config/evolution-effectiveness.yaml",
    ROOT / "scripts/evolution_effectiveness.py",
    ROOT / ".github/workflows/evolution-effectiveness.yml",
    ROOT / "tests/evidence/evolution_effectiveness_lifecycle.py",
    ROOT / "tests/scenarios/155-evolution-effectiveness-feedback-loop.md",
    ROOT / "orchestration/EVOLUTION_RADAR.md",
    ROOT / "docs/human/EVOLUTION_RADAR.md",
)
for path in required:
    if not path.exists():
        errors.append(f"Missing Evolution Effectiveness artifact: {path.relative_to(ROOT)}")

for rel in (
    "scripts/evolution_effectiveness.py",
    "tests/evidence/evolution_effectiveness_lifecycle.py",
):
    path = ROOT / rel
    if path.exists():
        compiled = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
        if compiled.returncode != 0:
            errors.append(f"Evolution Effectiveness syntax failed: {rel}: {compiled.stderr.strip()}")

config_path = ROOT / "config/evolution-effectiveness.yaml"
if config_path.exists():
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if config.get("version") != 1:
        errors.append("Evolution Effectiveness config version must be 1")
    authority = config.get("authority") or {}
    for key in (
        "automatic_source_weight_changes",
        "automatic_source_enable_disable",
        "automatic_config_mutation",
        "code_change_authorized",
        "branch_or_pr_authorized",
        "merge_authorized",
        "release_authorized",
    ):
        if authority.get(key) is not False:
            errors.append(f"Evolution Effectiveness must keep {key}=false")
    if authority.get("human_review_required_for_source_changes") is not True:
        errors.append("Evolution Effectiveness source-policy changes must remain Human-reviewed")

script_path = ROOT / "scripts/evolution_effectiveness.py"
if script_path.exists():
    script = script_path.read_text(encoding="utf-8")
    for contract in (
        "monthly_effectiveness",
        "REVIEW_HIGH_FAILURE_RATE",
        "REVIEW_LOW_SHORTLIST_YIELD",
        "REVIEW_ZERO_ACTIONABLE_AFTER_SEMANTIC",
        "AIPS_EVOLUTION_EFFECTIVENESS_START",
        "effectiveness_fingerprint",
        "automatic_source_weight_changes",
        "trial_handoff_ready_count",
        "adoption_count",
    ):
        if contract not in script:
            errors.append(f"Evolution Effectiveness script missing contract: {contract}")

workflow_path = ROOT / ".github/workflows/evolution-effectiveness.yml"
if workflow_path.exists():
    workflow = workflow_path.read_text(encoding="utf-8")
    for contract in (
        'cron: "15 2 2 * *"',
        "contents: read",
        "issues: write",
        "persist-credentials: false",
        "evolution_effectiveness.py build",
        "evolution_effectiveness.py validate",
        "evolution_effectiveness.py markdown",
        "Evolution Effectiveness [monthly]",
        "gh issue edit",
        "gh issue close",
        "gh issue reopen",
    ):
        if contract not in workflow:
            errors.append(f"Evolution Effectiveness workflow missing contract: {contract}")
    for forbidden in (
        "contents: write",
        "pull-requests: write",
        "git push",
        "gh pr create",
        "gh pr merge",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
    ):
        if forbidden in workflow:
            errors.append(f"Evolution Effectiveness workflow must remain credential-free/non-publishing: {forbidden}")

lifecycle = ROOT / "tests/evidence/evolution_effectiveness_lifecycle.py"
if lifecycle.exists():
    try:
        result = subprocess.run([sys.executable, str(lifecycle)], capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        errors.append("Evolution Effectiveness lifecycle timed out after 45 seconds")
    else:
        if result.returncode != 0:
            errors.append(f"Evolution Effectiveness lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
