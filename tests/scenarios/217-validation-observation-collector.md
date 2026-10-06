# Validation observation collector

Given the repository validation workflow produces a full-run shadow plan, validator timings, and an Integration Gate result,
When the workflow completes or fails,
Then one bounded observation retains candidate identity, prediction, actual validator outcomes, run-attempt provenance, and source digests for at least the 30-day graduation window,
And missing or mismatched evidence remains incomplete,
And the read-only collector deduplicates reruns to one latest record per pull request and invokes the existing graduation evaluator,
And the collector workflow installs the declared runtime and validation dependency profile under tested constraints and verifies its yaml import,
And full validation remains enabled and a ready report requires human review before any selective-execution change,
And a completed NOT_READY report is successful collection with an explicit evidence-gap summary,
And operational API or corrupt-artifact errors remain non-zero and are reported as ERROR,
And --require-ready opts into non-zero status when a completed report is NOT_READY.

Evidence: `scripts/validation_observation.py`, `.github/workflows/validate.yml`, `.github/workflows/validation-observation-collector.yml`, `tests/evidence/validation_observation_lifecycle.py`, and `tests/validation/validation_observation_contracts.py`.
