# Scenario 182 — Deterministic Execution Ownership

Each scheduled task has one execution owner bound to the canonical Task Graph, shared scheduler state, Change Boundary, declared read/write sets, and an active AIPS-managed worktree. Claims are serialized so concurrent workers cannot both claim overlapping boundaries. Task Graph v1 remains valid and ownership data is optional for legacy runs.

Heartbeat expiry marks the lease stale; dirty work is never reassigned automatically. Explicit recovery records its reason and requires acknowledgement before adopting dirty files. Completion compares staged, unstaged, untracked, moved and renamed paths against the write set and blocks any out-of-scope path. Read-only projections expose task, owner, boundary, worktree, dirty paths, dependency, heartbeat and enforcement capability without mutating state. Resource Authorization remains ADVISORY unless a runtime write guard is verified.
