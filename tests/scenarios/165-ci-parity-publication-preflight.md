# Scenario 165 — CI-Parity Publication Preflight

## Given

A publication candidate may include committed, staged, unstaged and untracked paths, and may affect documentation placement, change classification, Core Change matrix requirements, protected-branch routing, runtime validation capabilities and post-squash local state.

## When

The maintainer previews a working tree, binds the reviewed Core Matrix, then runs the shared publication preflight locally while GitHub validates the pull request and any classification-label changes.

## Then

- local and CI resolve the same exact base/head, change class and canonical matrix contract;
- preview includes untracked and uncommitted paths and explains why every documentation path is required;
- Core Matrix binding refresh updates base/hash and invalidates prior READY/reconciled state for review;
- the Gate fails if a test command reports fewer or more than its declared expected test count;
- adding or removing a change-class label triggers a fresh validation run;
- diff-aware documentation impact runs before expensive lifecycle validation;
- missing base or required documentation cannot be reported as CI-parity PASS;
- Git-ignored local metadata does not violate documentation audience layout;
- unsupported localhost/browser capabilities are reported as environment blockers;
- protected main routes through a pull request;
- post-merge reconciliation requires a clean tree, preserves a backup branch and resets only when tree objects are identical;
- Project Intelligence revision refresh occurs automatically only for equivalent trees; semantic changes remain fail-closed;
- publication, reset and merge authority remain Human-controlled.
