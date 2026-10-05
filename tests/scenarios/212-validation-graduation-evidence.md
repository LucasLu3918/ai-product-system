# Scenario 212: Selective validation graduation evidence

Given a full-run shadow cohort, when graduation evidence is evaluated, then incomplete artifacts, fewer than 30 observation days, an insufficient pull-request cohort, stale or mismatched plans, or any false-negative validator skip prevent readiness. Core, large, release, unknown, validator, and governance changes retain full validation; a deterministic SHA-based sample is recorded. A positive report is only `READY_FOR_HUMAN_REVIEW` and never enables selective execution.

Evidence: `tests/evidence/validation_graduation_lifecycle.py`, `tests/validation/validation_graduation_contracts.py`, and `scripts/validation_graduation.py`.
