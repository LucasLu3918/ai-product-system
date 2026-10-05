"""Static contract checks for monthly maintenance reliability reporting."""
from __future__ import annotations

from pathlib import Path

import yaml

from .static_contracts import ROOT, errors

config_path = ROOT / "config/maintenance-reliability.yaml"
workflow_path = ROOT / ".github/workflows/maintenance-reliability.yml"
script_path = ROOT / "scripts/maintenance_reliability.py"
evidence_path = ROOT / "tests/evidence/maintenance_reliability_lifecycle.py"

for path in (config_path, workflow_path, script_path, evidence_path):
    if not path.is_file():
        errors.append(f"Missing maintenance reliability artifact: {path.relative_to(ROOT)}")

if config_path.is_file():
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    collection = config.get("collection") or {}
    authority = config.get("authority") or {}
    if config.get("version") != 1 or collection.get("page_size") != 100:
        errors.append("Maintenance reliability config must use version 1 and GitHub's bounded page size")
    slo = config.get("slo_policy") or {}
    if slo.get("activation") != "deferred" or slo.get("thresholds_active") is not False:
        errors.append("Reliability SLO thresholds must remain deferred until sufficient history exists")
    if slo.get("minimum_complete_months_before_review") != 3 or slo.get("threshold_effect") != "human_review_flag_only":
        errors.append("Reliability SLO review must require three complete months and remain advisory")
    for key in ("max_pages", "max_failure_details", "max_pull_requests", "max_files_per_pull_request"):
        if not isinstance(collection.get(key), int) or collection[key] < 1:
            errors.append(f"Maintenance reliability collection.{key} must be a positive bound")
    for key in ("automatic_remediation", "automatic_code_change", "branch_or_pr_authorized", "merge_authorized", "release_authorized"):
        if authority.get(key) is not False:
            errors.append(f"Maintenance reliability authority.{key} must remain false")
    if authority.get("human_review_required") is not True:
        errors.append("Maintenance reliability must require Human review")

if workflow_path.is_file():
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8")) or {}
    permissions = workflow.get("permissions") or {}
    if permissions != {"actions": "read", "contents": "read", "issues": "write", "pull-requests": "read"}:
        errors.append("Maintenance reliability workflow must use only Actions/contents/PR read and review Issue write permissions")
    text = workflow_path.read_text(encoding="utf-8")
    for forbidden in ("contents: write", "pull-requests: write", "deployments: write", "git push", "gh pr merge"):
        if forbidden in text:
            errors.append(f"Maintenance reliability workflow contains forbidden authority: {forbidden}")
    if "schedule:" not in text or "workflow_dispatch:" not in text:
        errors.append("Maintenance reliability workflow must support monthly schedule and manual period selection")

if script_path.is_file():
    source = script_path.read_text(encoding="utf-8")
    for required in ("pass_rate_basis_points", "failure_categories", "escaped_regressions", "files_per_change", "nearest", "failure_details_complete"):
        if required not in source:
            errors.append(f"Maintenance reliability implementation is missing contract token: {required}")
    if "failure_categories" in source and "unknown" not in source:
        errors.append("Maintenance reliability failure category contract must preserve unknown outcomes")
