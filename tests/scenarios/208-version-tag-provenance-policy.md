# Scenario 208: Version tag provenance policy

Given VERSION, an exact requested release version and a candidate/main commit, when tag readiness is assessed, then only the exact main SHA with the matching VERSION can become ready for a separate explicit release approval; an existing mismatched tag is blocked, historical tags are not backfilled, and no tag is written. The manual release-readiness workflow collects this evidence with read-only permissions. Stable install and update stop when no verified release tag exists and never silently fall back to mutable main.

Evidence: `tests/evidence/version_policy_lifecycle.py`.
