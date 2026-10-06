from __future__ import annotations

from .static_contracts import ROOT, errors, load_yaml

path = ROOT / ".github/workflows/installation-entrypoints.yml"
workflow = load_yaml(path) or {}
triggers = workflow.get("on") or workflow.get(True) or {}
expected_timeouts = {
    "unix": 5,
    "linux-lifecycle": 10,
    "windows-contract": 10,
}
jobs = workflow.get("jobs") or {}

if set(jobs) != set(expected_timeouts):
    errors.append("installation entrypoints must retain the expected Unix, Linux lifecycle and Windows jobs")
for name, expected in expected_timeouts.items():
    job = jobs.get(name) or {}
    if job.get("timeout-minutes") != expected:
        errors.append(f"installation entrypoints {name} timeout must remain {expected} minutes until timing evidence is reviewed")

if "workflow_dispatch" not in triggers:
    errors.append("installation entrypoints must retain its manual workflow_dispatch trigger")
pull_request = triggers.get("pull_request") or {}
paths = set(pull_request.get("paths") or [])
if not {"scripts/install.sh", "scripts/install.ps1", "bin/aips"}.issubset(paths):
    errors.append("installation entrypoints must retain the install-script and CLI pull-request path filters")
if workflow.get("permissions") != {"contents": "read"}:
    errors.append("installation entrypoints must retain contents: read only")
if workflow.get("concurrency"):
    errors.append("independent installation entrypoint runs must not gain cancellation concurrency without shared-state evidence")
