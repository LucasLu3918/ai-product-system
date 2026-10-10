# Scenario 228 — Progressive Quality Ratchet

## Request

Add measured per-module debt and coverage evidence without tightening the repository-wide required threshold.

## Expected

- Existing Ruff and mypy gates keep their current limits.
- Ruff reports retain per-module budget evidence and lower next targets.
- Ruff's measured repository baseline is 687 findings; the Project Intelligence facade is at 0 and Retrieval Intelligence at 5 findings. The zero-finding facade uses a terminal zero budget that blocks any new finding.
- Coverage records the bounded Impact Graph relation-candidate lifecycle at 45.5% combined statement-and-branch coverage, while `minimum_percent` remains null and policy remains `report_only`.
- A narrow lifecycle measurement is not described as repository-wide coverage.

## Evidence

`tests/evidence/quality_ratchet_lifecycle.py` checks progressive Ruff debt behavior. `tests/validation/quality_ratchet_contracts.py` checks the exact bounded Impact Graph and storage lifecycle records and unchanged report-only policy. Impact Graph measurement: `coverage run --branch --source=project_intelligence_impact_graph tests/evidence/project_intelligence_relation_candidates_lifecycle.py`.
