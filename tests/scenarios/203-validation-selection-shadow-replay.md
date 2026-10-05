# Scenario 203: Validation selection shadow and replay

Given exact changed paths and a change class, when the advisory selector runs, then it fingerprints deterministic `would_run` and `would_skip` sets while every validator still executes. Unknown paths and Core/Large/Release classes retain full validation; replay evidence reports its supplied corpus and any false-negative recorded failures.

Evidence: `tests/evidence/validation_shadow_plan_lifecycle.py`.
