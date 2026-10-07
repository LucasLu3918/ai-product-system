# Scenario 228 — Progressive Quality Ratchet

## Request

Add measured per-module debt and coverage evidence without tightening the repository-wide required threshold.

## Expected

- Existing Ruff and mypy gates keep their current limits.
- Ruff reports retain per-module budget evidence and lower next targets.
- Coverage records a measured lifecycle baseline with exact scope, while `minimum_percent` remains null and policy remains `report_only`.
- A narrow lifecycle measurement is not described as repository-wide coverage.

## Evidence

`tests/evidence/quality_ratchet_lifecycle.py` checks progressive Ruff debt behavior. `tests/validation/quality_ratchet_contracts.py` checks the measured storage lifecycle baseline and unchanged report-only policy.
