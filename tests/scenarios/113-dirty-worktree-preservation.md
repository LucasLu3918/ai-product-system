# Scenario 113 — Dirty worktree cleanup is blocked

## Given
An AIPS-owned worktree has uncommitted changes.

## When
Cleanup is requested.

## Then
AIPS returns BLOCKED and preserves the worktree and user changes. Force removal is not performed.
