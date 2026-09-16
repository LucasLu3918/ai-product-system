# Scenario 116 — Canonical Repository and Workspace Identity

A repository has multiple Git worktrees.

Expected:
- all worktrees share one `repository_id`;
- each worktree has a distinct `workspace_id`;
- `aips identity` reports the same canonical identity as internal helpers;
- Project Intelligence, Run State and Isolation use the shared identity contract rather than unrelated path-hash schemes.
