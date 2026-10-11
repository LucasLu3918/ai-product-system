# Scenario 212: Selective validation graduation evidence

Given a full-run shadow cohort, when graduation evidence is evaluated, then incomplete artifacts, fewer than 30 observation days, fewer than 30 unique pull requests, stale or mismatched plans, or any false-negative validator skip prevent readiness. The report includes validator-level run precision, skip precision, recall, false-negative rate, confusion counts, and graduation thresholds; rates with zero denominators are null and do not imply zero risk. A one-day sample with no observed failures remains `NOT_READY`. Core, large, release, unknown, validator, and governance changes retain full validation; a deterministic SHA-based sample is recorded. A positive report is only `READY_FOR_HUMAN_REVIEW` and never enables selective execution.

Evidence: `tests/evidence/validation_graduation_lifecycle.py`, `tests/validation/validation_graduation_contracts.py`, and `scripts/validation_graduation.py`.
