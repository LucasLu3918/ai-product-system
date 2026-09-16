# Scenario 115 — Single writer per Change Boundary

## Given
An ACTIVE AIPS worktree already owns a Change Boundary.

## When
A second writable worktree is requested for the same project and boundary.

## Then
The second writer is blocked. Parallel read-only analysis/review remains a separate concern and is not prohibited.
