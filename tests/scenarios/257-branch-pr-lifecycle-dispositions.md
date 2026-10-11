# Scenario 257 — Branch and PR lifecycle dispositions

## Request

Review the current remote branches and open pull requests, and identify which items are still active, superseded, blocked by merge conflicts, or safe to review for cleanup.

## Expected

- Bind every report row to the current full branch SHA and target `main` SHA.
- Report `KEEP`, `SUPERSEDED`, `REBASE_REQUIRED`, or `CLEANUP_CANDIDATE` with its exact observed reason and PR evidence.
- Keep open, unmerged, persistent, unclassified, active-checkout, and unresolved work.
- Preserve the report-only boundary: do not close, rebase, merge, authorize, or delete any branch.
- Keep cleanup eligibility separate from exact-manifest approval and protected-main dispatch.

## Evidence

- `scripts/branch_hygiene.py`
- `tests/evidence/branch_hygiene_lifecycle.py`
- `tests/validation/branch_hygiene_contracts.py`
- `.github/workflows/branch-hygiene.yml`
