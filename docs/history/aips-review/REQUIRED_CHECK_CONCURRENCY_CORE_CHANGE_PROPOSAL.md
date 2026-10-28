# Core Change Proposal: Required Check Concurrency Isolation

## Problem

PR #296 had two `validate` workflow runs for the same head SHA: the `pull_request.opened` run and the `pull_request.labeled` run created when the Core classification label was added. Both used a concurrency group keyed only by PR number. The label run cancelled the opened run; the cancelled run did not produce the required `repository` aggregate, and GitHub kept the PR blocked until the missing run was rerun.

## Proposed change

- Add the triggering event action (or event name when no action exists) to the validate workflow concurrency group.
- Keep cancellation enabled for candidate events and Core/Large classification labels, disabled for unrelated label events, and scoped to the same PR plus event action.
- Update the static workflow contract to require distinct groups across PR actions and preserve the existing cancellation, Janitor, and aggregate behavior.
- Synchronize the required documentation closure and bind all evidence to the exact Core Change Matrix candidate.

## Boundaries and non-goals

No changes to branch protection, required check names, workflow permissions, full validation requirements, secret scanning, merge authority, tag creation, or release behavior. No administrative merge bypass. Runs from different actions may now execute concurrently; the exact-candidate aggregate remains responsible for rejecting stale or mismatched evidence.

## Expected impact

- Inputs: GitHub event name, pull-request number, and event action.
- Output: distinct workflow run identity for each PR action while retaining the `repository` aggregate context.
- Consumers: GitHub Actions concurrency cancellation and the existing required-check/branch-protection policy.
- Persistence/migration: none.
- Security: retain `contents: read`; no permissions or credential flow changes.
- Documentation: architecture, conformance, maintenance, security, technology and user guides; Core Change Testing, Deterministic Scheduler, Integration Gate, and Orchestrator.

## Verification

Run focused workflow static contracts, documentation impact/placement/link validation, VitePress build, complete repository validation, the exact-candidate secret scan and Core Integration Gate. Open a labeled PR and verify both action runs remain independent, all required checks pass, and the PR merges through the normal protected branch path.

## Approval

The user authorized optimizing the CI blocker and explicitly approved expanding the implementation to the 15-path documentation closure. Implement only this boundary; remote publication must follow the Git Publish Approval Gate, and merge must use normal GitHub policy.
