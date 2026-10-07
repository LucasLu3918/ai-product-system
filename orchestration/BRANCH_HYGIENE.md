# Branch Hygiene

## Read-only reconciliation

Run `python scripts/branch_hygiene.py --config config/branch-lifecycle.yaml --remote origin --pull-requests <read-only-gh-pr-list.json>` to classify the remote branch refs against the current default-branch SHA and exact merged-PR evidence. The report binds every observed branch to its current full SHA, distinguishes integrated ephemeral branches from branches that must be preserved, and emits a fingerprinted cleanup proposal for eligible entries.

`.aips/review/PLAN19_BRANCH_RECONCILIATION_DRAFT.yaml` is one such evidence snapshot. It records remote refs as observed at the embedded timestamp; the candidate list is proposal-only and must be refreshed if `main`, any listed ref, or GitHub PR evidence moves.

## Human authority

Branch count, age or ancestry alone never authorizes deletion. A proposal has `authorized: false`; this repository's reconciliation/report step does not delete branches. Any later cleanup requires explicit human approval of the exact one-time manifest, a fresh exact-SHA/integration preflight and the protected main-dispatch identity. Stale refs, missing merged-PR evidence, active local checkouts and unclassified branches are preserved.

The cleanup implementation uses an atomic push with exact SHA leases. Do not turn a report into a cleanup manifest or run an apply path without a separate human-approved exact manifest.
