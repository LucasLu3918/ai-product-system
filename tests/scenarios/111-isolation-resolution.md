# Scenario 111 — Execution isolation resolution

## Given
A Git project is processed by AIPS.

## When
The orchestrator resolves shared, worktree and sandbox execution modes.

## Then
- shared reports AVAILABLE but `isolated=false`;
- worktree reports AVAILABLE only when Git worktree capability is usable;
- sandbox reports UNSUPPORTED when no verified provider exists;
- no unsupported mode is silently represented as stronger isolation.
