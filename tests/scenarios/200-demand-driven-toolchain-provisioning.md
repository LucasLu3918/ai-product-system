# Scenario 200 — Demand-driven CI toolchain planning

## Intent

Provision optional CI toolchains from the exact changed-path set while retaining mandatory validation and fail-closed behavior.

## Expected behavior

- derive Node, browser and OpenAPI needs from exact Git candidate paths;
- select full optional tooling for unknown paths, planner errors and safety-critical workflow changes;
- keep secret scan, repository preflight, repository validation and exact-candidate Integration Gate required;
- skip only unrelated optional provisioning and explicitly report skipped OpenAPI lifecycle evidence;
- keep local validation on the full profile when no CI plan is supplied.

## Evidence

`tests/evidence/ci_validation_plan_lifecycle.py` checks docs-only, browser, OpenAPI, sensitive workflow and unknown-path plans.
