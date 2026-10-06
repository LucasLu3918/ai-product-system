from __future__ import annotations

from .static_contracts import ROOT, errors, load_yaml

caller_path = ROOT / ".github/workflows/validate.yml"
reusable_path = ROOT / ".github/workflows/dependency-review.yml"
caller = load_yaml(caller_path) or {}
reusable = load_yaml(reusable_path) or {}
jobs = caller.get("jobs") or {}
shadow = jobs.get("dependency-review-shadow") or {}
repository = jobs.get("repository") or {}

if shadow.get("uses") != "./.github/workflows/dependency-review.yml" or (shadow.get("with") or {}).get("shadow") is not True:
    errors.append("dependency review must explicitly request reusable shadow mode during the observation window")
if "continue-on-error" in shadow:
    errors.append("reusable workflow calls must not use unsupported job-level continue-on-error")
if shadow.get("permissions") != {"contents": "read", "pull-requests": "read"}:
    errors.append("dependency review shadow caller must grant only the reusable workflow's required read permissions")
if "workflow_call:" not in reusable_path.read_text(encoding="utf-8"):
    errors.append("dependency review must support reusable workflow invocation")
if "pull_request:" not in reusable_path.read_text(encoding="utf-8"):
    errors.append("dependency review must retain its standalone pull-request workflow")
if repository.get("needs") != "janitor":
    errors.append("dependency review shadow must not become required before parity evidence is collected")
if "standalone check remains authoritative during the observation window" not in reusable_path.read_text(encoding="utf-8"):
    errors.append("dependency review shadow must identify the standalone authoritative check")

if reusable.get("permissions") != {"contents": "read", "pull-requests": "read"}:
    errors.append("dependency review must retain read-only permissions")
review_job = (reusable.get("jobs") or {}).get("dependency-review") or {}
steps = review_job.get("steps") or []
action = next((step for step in steps if str(step.get("uses", "")).startswith("actions/dependency-review-action@")), {})
if action.get("uses") != "actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294":
    errors.append("dependency review must remain pinned to its reviewed action commit")
if (action.get("with") or {}).get("fail-on-severity") != "high":
    errors.append("dependency review must continue blocking high-severity dependency findings")
if action.get("continue-on-error") != "${{ inputs.shadow }}":
    errors.append("only the explicitly requested reusable shadow invocation may be non-blocking")
workflow_triggers = reusable.get("on") or reusable.get(True) or {}
workflow_call = workflow_triggers.get("workflow_call") or {}
shadow_input = ((workflow_call.get("inputs") or {}).get("shadow") or {})
if shadow_input.get("type") != "boolean" or shadow_input.get("default") is not False:
    errors.append("standalone dependency review must default to blocking when shadow mode is not requested")
if (shadow.get("with") or {}).get("shadow") is not True:
    errors.append("validation workflow must explicitly opt in to non-blocking shadow mode")
