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


## Evolution Trial use

A Human-approved Evolution `TRIAL` reuses this worktree isolation contract. The Trial workflow MUST request `worktree`; shared mode is not an allowed fallback.

The Trial worktree is ephemeral evidence infrastructure on the GitHub-hosted runner:

- checkout credentials are not persisted;
- the semantic execution provider receives no remote publication authority;
- the Human Decision supplies repository-relative approved path patterns;
- deterministic Trial evaluation rejects forbidden/out-of-scope paths, excessive diff size and any commit created inside the Trial;
- repository validation runs only after scope checks pass;
- Trial changes are not pushed and disappear with the runner;
- a Trial Report is returned to the Human before any adoption decision.

If worktree isolation is unavailable, the Trial is `BLOCKED`. Do not downgrade it to `shared`.


## Deterministic Scheduler integration

When one approved plan has multiple writer tasks, `orchestration/DETERMINISTIC_SCHEDULER.md` reuses this isolation/single-writer contract.

- each scheduled writable task declares canonical Change Boundary IDs;
- active worktree boundaries are locks;
- equal/ancestor/descendant boundaries conflict and are serialized;
- non-overlapping approved boundaries may consume separate parallel slots;
- the scheduler cannot widen scope or downgrade required isolation;
- stale/failed task state blocks dependent dispatch until normal replan/recovery rules resolve it.

This adds deterministic coordination; it does not create a second workspace ownership system.

## Scheduler write-boundary hardening

A Scheduler task is treated as potentially writable unless it explicitly declares `read_only: true`. A writable/unspecified task without a non-empty Change Boundary is `SCHEDULER BLOCKED` before dispatch.

An explicit read-only task may omit a writer boundary only when it has no `write_set` and does not declare writable isolation. This keeps Execution Isolation fail-closed when planning metadata is incomplete.


## Resource-scoped authorization

Execution Isolation answers **where** a task runs and enforces the existing single-writer boundary. It does not by itself answer which resources/operations an Agent may use inside that workspace.

When a task has material tool/resource access, pair the Execution Profile with `orchestration/RESOURCE_AUTHORIZATION.md`:

~~~text
Execution Profile
→ Isolation mode / Change Boundary
→ Resource Authorization Profile
→ deterministic pre-execution ALLOW / DENY evidence
→ runtime/tool execution when all other gates allow
~~~

The authorization profile defaults to DENY and can only narrow ordinary operations. It cannot grant merge, release, publication, destructive administration, Human approval or a wider Change Boundary.

## Runtime-security assessment boundary

Issue #79 keeps out-of-band anomaly evidence and semantic intent governance outside the active Execution Isolation / Resource Authorization enforcement path. They remain assessment candidates only.

If a future Human-approved Trial is created, anomaly analysis must consume bounded observable events rather than private chain-of-thought or secret values, and semantic intent output must be monotonic with Resource Authorization: it may DENY or ESCALATE an otherwise-allowed operation, but it must never widen a resource grant, Change Boundary, protected-operation authority or Human approval.

## Agent anomaly evaluation lane

Scenario 139 does not create another Execution Isolation mode and does not attach a detector to runtime execution. The benchmark reads committed synthetic fixtures and Resource Authorization policy, then emits post-execution evaluation evidence.

Because it performs no trial workspace mutation, it does not require a managed worktree. Any future Human-approved prototype that captures real runtime observable events or mutates integration code must return to the normal Controlled Trial / Change Boundary / worktree rules.

The evaluation cannot widen Resource Authorization, Change Boundary or Human authority and cannot automatically remediate observed anomalies.

## Observable-event integration Trial isolation

Scenario 140 executes deterministic replay only. It does not invoke an Agent to mutate a Trial worktree and does not attach a capture hook to a live runtime, so its Trial execution is read-only evidence generation over committed sanitized fixtures.

The Human Decision's approved mutation path remains bounded for any future agent-generated prototype, but the committed replay itself writes no source/runtime state.

Any future Trial that installs a real runtime capture hook, modifies adapter configuration, or creates Agent-authored prototype files must return to the normal managed worktree / Change Boundary / forbidden-path checks. A replay PASS cannot bypass those controls.

## Trial-backed adoption is not an execution workspace

Scenario 141 creates no Trial worktree and runs no live capture hook. It binds already committed PASS evidence to a current-baseline Human ADOPT Decision and System Improvement Review.

Any future implementation of `AGENT_OBSERVABLE_EVENT_CAPTURE_DESIGN.md` that mutates a runtime adapter or installs a runtime hook returns to the normal Execution Isolation rules: explicit Change Boundary, isolated writer where applicable, exact-candidate validation and no publication authority derived from the adoption artifact.

