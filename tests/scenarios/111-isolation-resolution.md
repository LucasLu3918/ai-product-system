# Scenario 111 — Execution isolation resolution

## Given
A Git project is processed by AIPS.

## When
The orchestrator resolves shared, worktree, sandbox or automatic isolation using risk and data-class inputs.

## Then
- shared reports AVAILABLE but `isolated=false`;
- worktree reports AVAILABLE only when Git worktree capability is usable;
- sandbox reports UNSUPPORTED when no verified provider exists;
- auto selects worktree for ordinary risk and requires sandbox for high/critical risk or explicitly untrusted execution;
- required sandbox that is unavailable remains UNSUPPORTED/BLOCKED and is never downgraded;
- no unsupported mode is silently represented as stronger isolation.
