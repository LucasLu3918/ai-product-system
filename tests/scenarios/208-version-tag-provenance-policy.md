# Scenario 208: Version tag provenance policy

Given VERSION and an exact candidate/main commit, when tag readiness is assessed, then only the exact main SHA can become ready for a separate explicit release approval; an existing mismatched tag is blocked, historical tags are not backfilled, and no tag is written.

Evidence: `tests/evidence/version_policy_lifecycle.py`.
