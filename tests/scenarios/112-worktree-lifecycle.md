# Scenario 112 — AIPS worktree lifecycle

## Given
A Git project and an unused isolation id / Change Boundary.

## When
AIPS creates worktree isolation.

## Then
- a real Git worktree is created outside the project source tree;
- an AIPS-owned record binds project, boundary, branch and path;
- status can verify the worktree and its revision;
- clean removal removes the worktree while preserving the managed branch.
