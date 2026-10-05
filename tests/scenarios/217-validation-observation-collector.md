# Validation observation collector

Given the repository validation workflow produces a full-run shadow plan, validator timings, and an Integration Gate result,
When the workflow completes or fails,
Then one bounded observation retains candidate identity, prediction, actual validator outcomes, run-attempt provenance, and source digests for at least the 30-day graduation window,
And missing or mismatched evidence remains incomplete,
And the read-only collector deduplicates reruns to one latest record per pull request and invokes the existing graduation evaluator,
And full validation remains enabled and a ready report requires human review before any selective-execution change.

Evidence: `scripts/validation_observation.py`, `.github/workflows/validate.yml`, `.github/workflows/validation-observation-collector.yml`, `tests/evidence/validation_observation_lifecycle.py`, and `tests/validation/validation_observation_contracts.py`.
