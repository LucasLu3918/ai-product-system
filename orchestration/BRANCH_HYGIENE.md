# Branch Hygiene

## Read-only reconciliation

Run `python scripts/branch_hygiene.py --config config/branch-lifecycle.yaml --remote origin --pull-requests <read-only-gh-pr-list.json>` to classify the remote branch refs against the current default-branch SHA and exact PR evidence. The report binds every observed branch to its current full SHA and emits a reasoned disposition:

- `KEEP` for persistent, unclassified, actively checked-out, open/unmerged, or otherwise unresolved work;
- `REBASE_REQUIRED` only when GitHub reports an open PR has merge conflicts;
- `SUPERSEDED` when the branch tree is already represented by the target but exact merged-PR evidence does not qualify it for cleanup;
- `CLEANUP_CANDIDATE` only for an ephemeral, inactive branch with exact merged-PR head evidence and target integration.

The disposition is advisory. It does not close a PR, rebase or merge a branch, generate an authorized cleanup manifest, or delete a ref. `disposition_evidence` records the branch and target SHAs, observed PR identity/state, integration result, and lifecycle classification. The workflow reads PR title/state/mergeability fields and publishes the same reason in its summary. Missing or malformed GitHub metadata blocks report generation.

`docs/history/aips-review/PLAN19_BRANCH_RECONCILIATION_DRAFT.yaml` is one such evidence snapshot. It records remote refs as observed at the embedded timestamp; the candidate list is proposal-only and must be refreshed if `main`, any listed ref, or GitHub PR evidence moves. `KEEP`, `SUPERSEDED`, `REBASE_REQUIRED`, and `CLEANUP_CANDIDATE` describe current evidence only; they are not branch ownership or authorization records.

## Human authority

Branch count, age or ancestry alone never authorizes deletion. A proposal has `authorized: false`; this repository's reconciliation/report step does not delete branches. Any later cleanup requires explicit human approval of the exact one-time manifest, a fresh exact-SHA/integration preflight and the protected main-dispatch identity. Stale refs, missing merged-PR evidence, active local checkouts and unclassified branches are preserved.

The cleanup implementation uses an atomic push with exact SHA leases. Do not turn a report into a cleanup manifest or run an apply path without a separate human-approved exact manifest.
