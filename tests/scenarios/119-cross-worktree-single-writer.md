# Scenario 119 — Single Writer Is Repository-wide Across Worktrees

One AIPS-managed worktree owns a Change Boundary.

A second request for the same repository and Change Boundary originates from another Git worktree.

Expected:
- the second writer is BLOCKED;
- ownership lookup includes compatible legacy AIPS isolation records when their repository can be verified;
- status/removal can be performed from another worktree of the same repository;
- cleanup still requires AIPS ownership, managed path, Git worktree membership and clean state.
