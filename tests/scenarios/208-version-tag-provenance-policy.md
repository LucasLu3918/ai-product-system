# Scenario 208: Version tag provenance policy

Given VERSION, an exact requested release version, a candidate/main commit and CHANGELOG.md, when tag readiness is assessed, then only the exact main SHA with the matching VERSION, no mismatched existing tag, and exactly one empty canonical `## Unreleased` section can become ready for a separate explicit release approval. A missing, duplicated, malformed or non-empty Unreleased section is blocked. Historical tags are not backfilled, and no tag is written. The manual release-readiness workflow collects this evidence with read-only permissions. Stable install and update stop when no verified release tag exists and never silently fall back to mutable main.

Evidence: `tests/evidence/version_policy_lifecycle.py`.
