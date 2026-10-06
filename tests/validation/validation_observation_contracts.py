from __future__ import annotations

from .static_contracts import ROOT, errors, load_yaml

script = ROOT / "scripts/validation_observation.py"
lifecycle = ROOT / "tests/evidence/validation_observation_lifecycle.py"
workflow = ROOT / ".github/workflows/validation-observation-collector.yml"
validate_workflow = ROOT / ".github/workflows/validate.yml"
graduation_config = load_yaml(ROOT / "config/validation-graduation.yaml")

for path in (script, lifecycle, workflow, validate_workflow):
    if not path.is_file():
        errors.append(f"Missing validation observation artifact: {path.relative_to(ROOT)}")

if graduation_config.get("mode") != "full_run_shadow":
    errors.append("Validation observation collection must preserve full-run shadow mode")
execution = graduation_config.get("execution") or {}
if execution.get("selective_execution_enabled") is not False or execution.get("automatic_activation_authorized") is not False:
    errors.append("Validation observation collection must not authorize selective execution")

if workflow.is_file():
    import yaml
    doc = yaml.safe_load(workflow.read_text(encoding="utf-8")) or {}
    permissions = doc.get("permissions") or {}
    collect_job = (doc.get("jobs") or {}).get("collect") or {}
    if collect_job.get("timeout-minutes") != 15:
        errors.append("Validation observation collector must retain its 15-minute provisional timeout")
    if "concurrency" in doc or "concurrency" in collect_job:
        errors.append("Validation observation collector must not replace pending scheduled or manual evidence runs")
    events = doc.get("on") or doc.get(True) or {}
    schedule = events.get("schedule") or []
    if len(schedule) != 1 or (schedule[0] or {}).get("cron") != "17 6 * * *":
        errors.append("Validation observation collector schedule must remain daily at 06:17 UTC")
    if "workflow_dispatch" not in events:
        errors.append("Validation observation collector must retain manual dispatch")
    if permissions.get("actions") != "read" or permissions.get("contents") != "read":
        errors.append("Validation observation collector must use read-only GitHub permissions")
    if any(value in {"write", "write-all"} for value in permissions.values()):
        errors.append("Validation observation collector must not receive write permissions")
    bootstrap = next((step for step in doc.get("jobs", {}).get("collect", {}).get("steps", [])
                      if step.get("uses") == "./.github/actions/aips-python-bootstrap"), {})
    if bootstrap.get("with", {}).get("requirements-files", "").splitlines() != ["requirements.txt", "requirements-validation.txt"]:
        errors.append("Validation observation collector must use the shared runtime and validation dependency profile")
    if bootstrap.get("with", {}).get("constraints-file") != "constraints/tested.txt":
        errors.append("Validation observation collector must retain tested dependency constraints")

if validate_workflow.is_file():
    text = validate_workflow.read_text(encoding="utf-8")
    if "Capture combined validation observation" not in text or "retention-days: 90" not in text:
        errors.append("Validate workflow must retain combined observations for at least 90 days")
    import yaml
    workflow_doc = yaml.safe_load(text) or {}
    jobs = workflow_doc.get("jobs") or {}
    fast_lane = jobs.get("advisory-fast-feedback") or {}
    if not fast_lane:
        errors.append("Validate workflow must run a separate advisory fast-feedback job")
    else:
        if fast_lane.get("needs"):
            errors.append("Advisory fast feedback must run independently of the required repository gate")
        if fast_lane.get("timeout-minutes") != 10:
            errors.append("Advisory fast feedback must have a bounded ten-minute timeout")
        condition = str(fast_lane.get("if") or "")
        if "pull_request" not in condition or "labeled" not in condition or "unlabeled" not in condition:
            errors.append("Advisory fast feedback must run only for non-label pull-request events")
        env = fast_lane.get("env") or {}
        if "pull_request.base.sha" not in str(env.get("AIPS_GATE_BASE")) or "pull_request.head.sha" not in str(env.get("AIPS_GATE_HEAD")):
            errors.append("Advisory fast feedback must bind both exact pull-request SHAs")
        steps = fast_lane.get("steps") or []
        preflight = next((step for step in steps if step.get("id") == "fast_preflight"), {})
        if preflight.get("continue-on-error") is not True or "scripts/repository_preflight.py" not in str(preflight.get("run") or ""):
            errors.append("Advisory fast-preflight findings must be reported without blocking the full required gate")
    if "AIPS_FAST_PREFLIGHT_OUTCOME" not in text:
        errors.append("Advisory fast-feedback findings must be reported without blocking the full required gate")
    if "--base \"$AIPS_GATE_BASE\" --head \"$AIPS_GATE_HEAD\"" not in text:
        errors.append("Advisory fast feedback must inspect the exact pull-request candidate")
    permissions = workflow_doc.get("permissions") or {}
    if permissions.get("contents") != "read" or any(value in {"write", "write-all"} for value in permissions.values()):
        errors.append("Validation workflow and advisory feedback must remain read-only")
    repository = jobs.get("repository") or {}
    if repository.get("needs") != "janitor":
        errors.append("Required repository validation must remain unchanged during dependency review shadow")
    dependency_review = jobs.get("dependency-review-shadow") or {}
    if dependency_review.get("uses") != "./.github/workflows/dependency-review.yml" or (dependency_review.get("with") or {}).get("shadow") is not True or "continue-on-error" in dependency_review:
        errors.append("Dependency review must request its advisory parity shadow through the reusable workflow input")
    if "--require-ready" not in script.read_text(encoding="utf-8"):
        errors.append("Observation collection must provide explicit opt-in require-ready semantics")
    if "READY_FOR_HUMAN_REVIEW" not in str(workflow.read_text(encoding="utf-8")) or "NOT_READY" not in str(workflow.read_text(encoding="utf-8")):
        errors.append("Observation workflow summary must distinguish ready and not-ready reports")
    collector_text = workflow.read_text(encoding="utf-8")
    if 'if [[ ! -s "$AIPS_REPORT" ]]' not in collector_text or "unknown report status" not in collector_text or "operational collection failed" not in collector_text:
        errors.append("Observation workflow must fail closed for missing reports, unknown states and operational errors")

if lifecycle.is_file():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, str(lifecycle)], capture_output=True, text=True, check=False)
    if result.returncode:
        errors.append(f"Validation observation lifecycle failed: {result.stdout.strip()} {result.stderr.strip()}")
