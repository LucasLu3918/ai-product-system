# Parallel advisory fast feedback

Given a pull request candidate, when the validation workflow starts, then a separate bounded repository-preflight job checks the exact head concurrently with the existing validation path,
And fast-lane findings are summarized as advisory and cannot fail or replace the required full repository gate,
And unrelated label-only events do not rerun the advisory job.

Evidence: `.github/workflows/validate.yml`, `scripts/repository_preflight.py`, and `tests/validation/validation_observation_contracts.py`.
