# Execution Isolation

Execution isolation is a capability of the existing Execution Profile. It is not a Role, Skill or approval gate.

## Modes

- `shared` — use the existing project workspace. Available by default, but it is not an isolation boundary.
- `worktree` — use a real Git worktree managed by AIPS. This is the default isolated writer workspace when Git worktree support is available.
- `sandbox` — use a verified external sandbox provider. AIPS core does not emulate sandboxing with a temporary directory.

## Resolution

Resolve isolation before mutation when independent writer state, risky experimentation, or concurrent read/review work makes workspace separation useful.

Truthful capability reporting is mandatory:

- shared → AVAILABLE, isolated=false;
- worktree → AVAILABLE only when the target is a Git repository and `git worktree` is usable;
- sandbox → UNSUPPORTED unless a verified provider integration exists.

Unsupported isolation must become explicit BLOCKED/UNSUPPORTED state. Never silently downgrade a requested sandbox to shared or a temp directory.

## Worktree ownership

AIPS-created worktrees live outside the project source tree:

`~/.config/aips/worktrees/<repository-id>/<isolation-id>/`

Ownership records live at:

`~/.config/aips/isolation/<repository-id>/<isolation-id>.yaml`

Each record binds repository_id, workspace identity, isolation id, Change Boundary, branch, path and base revision.

Creation uses a dedicated `aips/isolation/<id>` branch. Cleanup removes only the worktree; the branch is preserved so committed work is not deleted implicitly.

## Single writer per Change Boundary

Parallel analysis and review remain allowed. A writable Change Boundary has one active writer by default.

Before creating a worktree, AIPS scans active AIPS-owned isolation records for the same repository_id and Change Boundary, including verifiable legacy records from another worktree. A second active writer for that boundary is BLOCKED.

Isolation does not authorize broader scope. Governance, approval binding, Change Impact and test obligations still apply exactly as they do in shared mode.

## Safe cleanup

AIPS removes only AIPS-owned worktrees under the managed worktree root.

Cleanup must stop when:

- the record is not AIPS-owned;
- the path is outside the managed root;
- cleanliness cannot be verified;
- the worktree has uncommitted changes.

Dirty worktrees are preserved and reported BLOCKED. AIPS never force-removes them.

## CLI

~~~bash
aips isolation resolve --project /path/to/project --mode shared
aips isolation resolve --project /path/to/project --mode worktree
aips isolation resolve --project /path/to/project --mode sandbox

aips isolation create --project /path/to/project --id change-123 --boundary orders
aips isolation status --project /path/to/project --id change-123
aips isolation remove --project /path/to/project --id change-123
~~~

The helper emits YAML by default and supports `--format json` for deterministic orchestration.
