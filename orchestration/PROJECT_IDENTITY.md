# Project / Workspace Identity

AIPS uses one canonical identity contract across Project Intelligence, Run State, Change Impact and Execution Isolation.

## Identity levels

`repository_id` identifies repository lineage for repository-wide coordination.

`workspace_id` identifies one active workspace/worktree inside that repository lineage.

~~~text
repository
├── repository_id
├── main worktree      → workspace_id A
├── feature worktree   → workspace_id B
└── AIPS worktree      → workspace_id C
~~~

`project_id` is retained as a compatibility alias for `workspace_id`.

## Derivation

For Git repositories:

1. prefer the configured `remote.origin.url` as repository lineage input;
2. when no remote exists, use the resolved Git common directory as the local lineage input;
3. derive the worktree component from the current root + Git directory;
4. hash only normalized identity inputs; do not persist credentials or repository file contents in identity metadata.

A repository without a stable remote cannot preserve lineage identity across arbitrary filesystem moves. AIPS must not claim otherwise.

## Storage rules

Workspace-scoped state uses `workspace_id`:

~~~text
~/.config/aips/projects/<workspace-id>/intelligence/
~/.config/aips/projects/<workspace-id>/runs/
~~~

Repository-wide writer coordination uses `repository_id`:

~~~text
~/.config/aips/isolation/<repository-id>/
~/.config/aips/worktrees/<repository-id>/
~~~

This prevents separate worktrees of one repository from acquiring conflicting writers for the same Change Boundary.

## Workspace fingerprint

Run Resume uses a content-derived workspace fingerprint:

- repository_id;
- workspace_id;
- Git HEAD;
- branch;
- staged/unstaged tracked diff;
- non-ignored untracked product files.

AIPS-owned `.ai/` and detached AIPS workspace state are excluded so checkpoint writes do not stale themselves.

Raw diffs and file contents are hashed for comparison and are not persisted in the checkpoint.

## Legacy compatibility

- existing remote-backed Project Intelligence IDs remain compatible with the previous algorithm where possible;
- legacy EPHEMERAL run state stored under the old absolute-path hash is migrated lazily per run when the canonical destination is absent;
- legacy Isolation ownership records remain discoverable when their repository association can still be verified;
- migration never silently overwrites an existing canonical destination.

Use `aips identity --project <path>` to inspect the resolved identity/fingerprint contract.
