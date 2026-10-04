# Scenario 201: Monthly maintenance reliability evidence

## Intent

Give maintainers a bounded, reproducible monthly view of validation outcomes, runtime distribution, explicitly labeled hotfixes, repeated changed surfaces, operational failure categories, escaped regressions and files per merged change.

## Acceptance

- Collect only bounded GitHub Actions validation-run and merged pull-request metadata for a selected calendar month.
- Report validation pass rate, median and nearest-rank P95 runtime, explicit normalized Hotfix labels, repeated file paths, configured failure categories, exact merge-SHA escaped regressions, and median/P95 files per change.
- When run, pull request, file, or failure-detail history is truncated or unavailable, or an eligible run lacks duration timestamps or a merged PR lacks its changed-file count, publish affected metrics as UNKNOWN/null and set a review flag instead of implying complete coverage.
- Persist only normalized metadata and file paths needed for metrics; do not persist logs, prompts, secrets, or raw API responses.
- Publish a deterministic report, Job Summary, bounded artifact, and deduplicated monthly review Issue.
- Keep the workflow read-only for repository contents and require Human review; it cannot remediate, change code, create PRs, merge, or release.

## Executable evidence

`tests/evidence/maintenance_reliability_lifecycle.py` verifies metric definitions, pagination response shapes, exact-SHA correlation, partial-history UNKNOWN behavior and deterministic output. `tests/validation/maintenance_reliability_contracts.py` verifies collection bounds and workflow authority.

## Limits

Failure categories are job/step-name keyword hints, not root-cause diagnosis. Escaped-regression linkage requires an exact failing `main` push SHA matching a merged pull request. These metrics are operational evidence for Human review and do not authorize automatic policy changes.
