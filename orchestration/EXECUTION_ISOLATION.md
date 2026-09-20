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

## Gemini CLI AfterTool capture Trial isolation

Scenario 142 installs a source-controlled `AfterTool` hook into the existing Gemini CLI extension, but it does not create a writable Agent Trial workspace.

The capture lane is isolated from normal project state by default:

- capture is disabled unless explicitly enabled;
- the sink must be an absolute path below the system temporary directory;
- raw Gemini hook input is never persisted;
- the bounded sink is owner-only and size-limited;
- capture degradation does not change or block the original tool result;
- no commit, branch, publication or runtime-remediation authority is derived from captured evidence.

If a later verification executes a real Gemini CLI binary, that verification must use an exact candidate and an isolated disposable project/workspace. A successful hook invocation still does not authorize production persistence or broader tool matchers.

## Gemini CLI exact-candidate runtime verification isolation

Scenario 143 executes a pinned Gemini CLI binary only inside the GitHub Actions runner's temporary HOME and workspace. The verifier links the exact-candidate Gemini extension through the same `~/.gemini/extensions` discovery path used by the runtime, but the test workspace contains only synthetic verification files.

The runtime workflow:

- checks out the exact pull-request head SHA;
- uses deterministic fake model responses and no provider credential material;
- performs real built-in `read_file`, `write_file`, and `replace` operations only inside a temporary workspace;
- writes observable-event evidence only to a temporary sink;
- keeps runtime enforcement, remediation, merge, release, publication and Human-approval authority false.

Gemini extension hook wrappers resolve their physical source path before locating the repository so symlink-based extension loading cannot redirect hook execution toward the temporary HOME.

## Gemini provider-session credential isolation

Live provider verification uses the already-verified Gemini CLI runtime path, but the provider credential adds a separate isolation boundary.

A bounded provider-session Trial MUST run only after its verification infrastructure is trusted on protected main. Unmerged PR code must not receive the provider credential. Temporary HOME/workspace and capture sink remain disposable, and only metadata evidence may persist.

A missing optional provider credential records `SKIPPED_NOT_CONFIGURED` / `NOT_CONFIGURED_BY_POLICY`. It must not be downgraded to fake-response provider evidence, treated as provider verification, or used to block unrelated baseline/release work.

<!-- AIPS_PROVIDER_CREDENTIAL_POLICY_V1 -->
## Optional External Credential Boundary

External Agent/provider credentials are not baseline execution requirements. A credential-dependent lane must remain disabled until the exact credential is explicitly configured. An absent optional credential is a normal `SKIPPED_NOT_CONFIGURED` state and must not expand authority, trigger alternate login flows, or block unrelated deterministic/runtime work.

No OAuth, Vertex AI, OIDC/WIF, or other replacement authentication is enabled by this policy.

## External Credential Dependency Guard isolation

The dependency guard never resolves or reads credential values. It inspects repository source/configuration references only.

A credential-free/default execution lane must not inherit an external provider secret merely because that secret exists in the repository secret store. Secret injection remains scoped to the explicit credential-dependent step or workflow branch, and pull-request code must not receive external provider credentials.

## Evolution Radar local pre-analysis isolation

The deterministic pre-analysis is a read-only evidence transform. It does not create a Trial worktree, invoke an Agent provider, mutate project source, or perform any additional network access.

Its inputs are bounded to committed configuration/Capability Map plus the already-collected Radar evidence. Output may be published into the Human review Issue as advisory triage metadata, but it grants no code-write, branch/PR, merge, release, publication, Human-decision, runtime-enforcement, or remediation authority.

## Repository Health interaction

Repository Health / Architecture Drift is read-only validation evidence. It may inspect source-controlled files and invoke Scenario Conformance, but it creates no execution workspace, claims no writer boundary, performs no remediation, and grants no runtime, code-change, PR, merge, release or publication authority.

## Evolution Radar quarterly review isolation

Quarterly Evolution Radar review is aggregation-only. It consumes durable monthly Issue evidence and MUST NOT initiate another public-source collection, provider/model execution, Trial workspace mutation or formal implementation branch. Its output remains evidence-only with protected-operation authority false.

