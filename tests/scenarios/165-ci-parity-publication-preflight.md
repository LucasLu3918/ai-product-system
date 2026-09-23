# Scenario 165 — CI-Parity Publication Preflight

## Given

A committed publication candidate may affect code, documentation placement, change classification, Core Change matrix requirements, protected-branch routing, runtime validation capabilities and post-squash local state.

## When

The maintainer runs the shared publication preflight locally and GitHub validates the pull request.

## Then

- local and CI resolve the same exact base/head, change class and canonical matrix contract;
- diff-aware documentation impact runs before expensive lifecycle validation;
- missing base or required documentation cannot be reported as CI-parity PASS;
- Git-ignored local metadata does not violate documentation audience layout;
- unsupported localhost/browser capabilities are reported as environment blockers;
- protected main routes through a pull request;
- post-merge reconciliation requires a clean tree, preserves a backup branch and resets only when tree objects are identical;
- Project Intelligence revision refresh occurs automatically only for equivalent trees; semantic changes remain fail-closed;
- publication, reset and merge authority remain Human-controlled.
