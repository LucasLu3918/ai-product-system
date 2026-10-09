# Execution Isolation

Runtime Context 會辨識 source checkout、linked worktree 與 installed system，並回報 offline 能力旗標；它只描述執行環境，不授予新的隔離或資源權限。

Execution isolation is a capability of the existing Execution Profile. It is not a Role, Skill or approval gate.

## Modes


- `shared` — use the existing project workspace. Available by default, but it is not an isolation boundary.
- `worktree` — use a real Git worktree managed by AIPS. This is the default isolated writer workspace when Git worktree support is available.
- `sandbox` — use a verified external sandbox provider. AIPS core does not emulate sandboxing with a temporary directory. A provider is eligible only when a current registry-bound record proves the required observed controls.

## Resolution

Resolve isolation before mutation when independent writer state, risky experimentation, or concurrent read/review work makes workspace separation useful.


Truthful capability reporting is mandatory:

- shared → AVAILABLE, isolated=false;
- worktree → AVAILABLE only when the target is a Git repository and `git worktree` is usable;
- sandbox → UNSUPPORTED when no provider is enabled; BLOCKED when an enabled provider lacks fresh matching verification or fails a required data/capability constraint; AVAILABLE only after a fresh matching verification.

Unsupported isolation must become explicit BLOCKED/UNSUPPORTED state. Never silently downgrade a requested sandbox to shared or a temp directory.

### Verified provider policy

`config/sandbox-providers.yaml` is the provider-neutral capability registry. Provider statements about MicroVM and hardware virtualization are marked provider-declared; AIPS receipts separately record controls observed by the integration. Registry changes invalidate prior verification by digest. Verification expires after the configured age.

Resolution accepts an explicit data class and minimum isolation class. The initial E2B candidate is disabled, accepts only `public` data, uses deny-all egress, has no host mounts, guest credentials or publication authority, and has a bounded TTL. `internal`, `confidential` and `restricted` data remain blocked until a policy-approved provider is configured. The `auto` resolver chooses worktree for ordinary risk and sandbox for high/critical risk or explicitly untrusted execution; it never falls back when sandbox is required but unavailable.

The optional E2B smoke test handles synthetic content only and emits a bounded receipt. The protected-main `workflow_dispatch` requires explicit confirmation that the provider's prior written testing consent was obtained. PRs do not receive `E2B_API_KEY`; missing credentials report `SKIPPED_NOT_CONFIGURED`. Smoke-test success does not enable the registry or attest the provider's underlying hypervisor. General task-file staging/execution remains disabled pending explicit data-scope authorization and implementation of its adapter; the registry's `integration_status` must be `AVAILABLE` before resolution can report `AVAILABLE`.

Guest artifacts must be treated as untrusted: validate relative paths and contents on the host, bind import to the source revision and Change Boundary, and run the existing Integration/Security Gate before Git operations. Sandbox capability grants no Git publication or deployment authority.
Regardless of workspace isolation mode, every Remote Git publication candidate must also pass the built-in strict secret scan over its final tree and full `base..head` history; a sandbox does not replace this publication check.

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


Local publication checks execute only the selected prepared Python environment and already-installed VitePress bundle. They do not invoke package managers or reach package registries; host/browser/loopback limits are reported as environment blockers before candidate lifecycle tests.

Lifecycle validator 子程序使用 `sys.executable`，避免呼叫主機上未安裝或缺少相依套件的泛用 `python` / `python3` 命令。

Portable Command projections 位於 AIPS-managed commands scope，透過 ownership manifest 與 digest 進行安全更新；使用者修改的 projection 不會被 uninstall 或 upgrade 覆寫。
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

An `INDEPENDENT_REVIEW` task runs under a distinct execution identity with `read_only: true`, a bounded allowlisted packet, and no inherited implementation conversation, hidden reasoning, scratchpad, or raw trace. Its evidence binds the exact candidate and packet digest. The Scheduler and Integration Gate must preserve `UNVERIFIED` when a trusted runtime attestation verifier is unavailable; required review then blocks the Gate.

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

Runtime Policy Enforcement may require provider-observed network allowlist evidence for protected external egress. The existing E2B candidate is disabled and deny-all; it does not currently authorize external egress. A pre-tool hook is not a substitute for sandbox network control.

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

Its implementation is isolated in `scripts/evolution_preanalysis.py`; callers continue through the `scripts/evolution_analysis.py` facade with identical read-only and authority boundaries.

Its inputs are bounded to committed configuration/Capability Map plus the already-collected Radar evidence. Output may be published into the Human review Issue as advisory triage metadata, but it grants no code-write, branch/PR, merge, release, publication, Human-decision, runtime-enforcement, or remediation authority.

## Repository Health interaction

Repository Conformance counts include the registered isolation lifecycle cases; changing that inventory requires updating its shared validation assertion and current Human/Agent Conformance records. Count registration proves coverage bookkeeping, not sandbox isolation.

Trajectory traces 與 evidence bundle 應在既有 execution boundary 內產生；評估器為 post-execution evidence，不建立新的 writer boundary、不執行自動 remediation，也不授予 publication authority。

Repository Health / Architecture Drift is read-only validation evidence. It may inspect source-controlled files and invoke Scenario Conformance, but it creates no execution workspace, claims no writer boundary, performs no remediation, and grants no runtime, code-change, PR, merge, release or publication authority.

## Evolution Radar quarterly review isolation

Quarterly Evolution Radar review is aggregation-only. It consumes durable monthly Issue evidence and MUST NOT initiate another public-source collection, provider/model execution, Trial workspace mutation or formal implementation branch. Its output remains evidence-only with protected-operation authority false.

The scheduled quarterly run is on day 3 of January, April, July and October so monthly source reports can publish first. Missing monthly bundles remain incomplete evidence and do not authorize Trial or implementation.



## Technology Intelligence boundary

Evolution Radar v0.43 expands research discovery and bounded semantic selection only. Community collection, deterministic pre-analysis, scoped semantic analysis and primary-corroboration checks do not create an execution boundary and cannot mutate a workspace. Controlled Trial isolation continues to start only after an explicit Human TRIAL Decision and retains the existing worktree, path, diff, validation and publication restrictions.


## Evolution evidence-quality boundary


Evidence-quality classification is a read-only deterministic transform over collected source provenance. It does not create or select an execution workspace, and it does not authorize a Controlled Trial. A higher evidence level may make a signal eligible for advisory semantic `ADOPT`, but any actual mutation still requires the existing Human Decision and Execution Isolation contracts. Semantic providers cannot upgrade evidence metadata to obtain broader execution authority.


## Provider-neutral Trial handoff isolation

`TRIAL_HANDOFF_READY` does not weaken the isolation contract. It records that execution has been handed to a Human-selected compatible provider; it does not create a shared-workspace fallback and it is not a PASS/BLOCKED Trial result.

The external executor is required to honor the exact `worktree` isolation requirement, approved path patterns, forbidden paths and change limits from the bound Trial Plan. Any eventual Trial claim must return to AIPS deterministic diff/commit/repository validation before PASS/FAIL evidence can be accepted. An external provider cannot widen the Change Boundary or gain publication credentials through the handoff.


## Evolution Effectiveness isolation boundary
Archived Radar Issue bodies are untrusted durable input. The decoder enforces an 8 MiB output ceiling and verifies SHA-256 before returning the original body to parsers; malformed, unsupported, or oversized payloads remain unavailable evidence and create no execution or authority boundary.


Effectiveness analysis is a read-only deterministic evidence aggregation over already-published Evolution Radar Issues and comments. It creates no Trial worktree, invokes no execution provider, and mutates no repository source.

The scheduled workflow may create/update/close/reopen its own GitHub effectiveness Issue using `issues: write`, but has only `contents: read`. Scheduled and same-period manual runs share a bounded non-cancelling queue; custom cohorts remain independent. Review flags cannot reweight, enable, disable or replace sources and cannot authorize a Trial, code change, PR, merge or release.


## Historical Evolution Issue reconciliation boundary

Closing/reconciling a stale Radar Issue is evidence lifecycle maintenance only. It creates no execution workspace, Trial authorization, runtime hook, enforcement path or remediation authority. Any deferred candidate that later becomes active must re-enter the normal current-baseline Human Decision + Controlled Trial + Execution Isolation flow.


## Parallel runtime resource isolation

OpenCode creative visual assistance is separately authorized by the current user prompt and confined to the active Session root; local model findings remain advisory and cannot broaden the execution grant.

Creative Session continuation is an in-memory policy boundary, not an OS process sandbox. Provider execution retains its existing EPHEMERAL path checks, allowlisted command mapping, loopback-only ComfyUI access and explicit user authorization.

Synthetic creative provider runs validate workflow contracts only; real inference and image quality require separate evidence.


The Creative `generate-set` executor processes configured Bundles sequentially within the active local project scope and records per-item recovery state; the OpenCode grant is in-memory and session-root-bound.

`aips project diagnose` performs local read-only inspection and does not select an isolation provider, launch a subprocess-backed task, or claim sandbox enforcement. Use the existing isolation resolver for execution decisions.

Local creative configure is a confined persistent effect even though it does not generate. Discovery and preflight stay read-only; execute remains explicit and local-only. No action changes the existing Shell/MCP coverage limitation or grants model-download authority.

The optional local MFLUX adapter is not a verified sandbox: its fixed child-process command and offline flags restrict behavior, but do not claim host-process isolation. It is never installed or executed by preflight or the Integration Gate.

Creative Bundle output is restricted to a non-Git EPHEMERAL project root and a declared create-only output directory; it does not create an execution sandbox or install an engine.

The OpenCode Shell hook uses semantic command/effect checks and is not an OS process sandbox; MCP/custom tools and other processes remain outside its observed boundary.

The OpenCode Shell hook performs semantic command/effect checks; it does not isolate processes, MCP/custom tools, or effects from other programs.

The OpenCode native file guard confines supported direct resources but is not an OS sandbox and does not constrain arbitrary subprocess, MCP, or out-of-process effects.

OpenCode native acceptance uses isolated HOME/XDG/config directories and a private loopback server. Test infrastructure must not change the user daemon or import provider credentials.

Run Dashboard path and digest projections preserve their existing facades over shared primitives; isolation, port leasing and authorization boundaries do not change.

Task-specific protocol routing precedes isolated execution but grants no worktree or sandbox capability; isolation still resolves from the declared risk and supported provider evidence.

Repository governance snapshots are read-only operator evidence and do not acquire write credentials or alter branch protection.

Explicit validation Python/venv selection cannot silently fall back. Verify coverage, Hypothesis, mandatory JSON Schema and pip consistency before full validation; telemetry requires loopback even without browser. Child executors preserve HOME/credential lookup while removing inherited plan/import overrides and binding PATH to the selected Python.

Each workflow job installs only its declared Python requirement profile under tested constraints and verifies its own imports and dependency consistency.

The AIPS CLI facade loads its internal modules from the resolved checkout before dispatch. Module extraction does not change worktree ownership, execution isolation mode or runtime resource policy.

The Validation Observation Collector has only read access to Actions and repository metadata. Artifact downloads are bounded, redirect credentials are not forwarded, and collection cannot write repository settings, branches or validation policy.

Coverage and Hypothesis lifecycle checks use the existing isolated validation Python process; they introduce no runtime service, network call, or cross-run resource sharing.

Evolution analysis persistence is an Issue-body handoff only after exact evidence and decision validation; scheduled workflow state does not grant additional write authority. Missing issue history or incomplete source cohorts remain visible as incomplete evidence.

Observed Context, Retrieval and Gate stages record only bounded operation names, outcome and measured duration. The recorder uses the existing run event stream; it does not capture prompts, tool arguments or private reasoning, and missing run state remains non-blocking.

The read-only dashboard aggregates known workspaces by repository identity and reports workspace health without changing ownership, isolation mode or writer boundaries.

A worktree separates Git/filesystem state, but parallel tasks can still collide on host runtime resources such as a development-server TCP port. Runtime Resource Lease extends the existing Execution Isolation ownership lifecycle; it is not a second isolation subsystem.

The scheduled Python compatibility workflow runs repository-owned installation lifecycle fixtures on GitHub-hosted runners with `contents: read`; it does not execute product-project code or claim an external sandbox boundary.

~~~text
scheduled task
→ AIPS-owned worktree
→ runtime port request
→ repository-scoped atomic lease registry
→ host bind availability probe
→ runtime environment manifest
→ Agent/dev server
~~~

The v0.51 contract supports TCP ports only.

- leases live under the external AIPS config root at `runtime/<repository-id>/ports.yaml`, never in project source;
- allocation is serialized by an atomic directory lock so concurrent AIPS processes cannot commit the same lease;
- candidate order is deterministic from repository/isolation/resource identity, while actual allocation also respects current host availability;
- `preferred` is a hint, not a guaranteed port;
- the canonical environment is `AIPS_PORT_<RESOURCE>`; when one port is leased, `AIPS_PORT` is also emitted;
- project/runtime adapters may request explicit aliases such as `PORT` through `--expose PORT` / Task Graph `expose_as`;
- the availability probe checks the host immediately before the lease is recorded, but no userspace pre-check can eliminate all TOCTOU races with non-AIPS processes;
- if startup still reports an address-in-use error, `runtime-reallocate` excludes the previous lease and performs a bounded retry;
- runtime release is independent from worktree cleanup, so a dirty worktree may remain preserved while its stopped server port is released;
- normal clean `isolation remove` also releases that isolation's runtime leases;
- `runtime-reconcile` removes only leases whose AIPS isolation record is no longer ACTIVE. It never guesses that an ACTIVE-but-idle lease is stale.

CLI:

~~~bash
aips isolation create --project /repo --id frontend-a --boundary apps-a \
  --port dev --preferred 3000 --expose PORT

aips isolation runtime-lease --project /repo --id frontend-b --port dev --expose PORT
aips isolation runtime-reallocate --project /repo --id frontend-b --port dev
aips isolation runtime-release --project /repo --id frontend-b --port dev
aips isolation runtime-reconcile --project /repo
~~~

A lease is coordination evidence, not authority. It does not authorize network access, publication, destructive operations, a wider Change Boundary, or bypass Resource Authorization.

Task ownership binds the dispatched task lease to its active AIPS-managed worktree and isolation ID. The scheduler state serializes competing claims across runs; lease expiry never transfers dirty work. Recovery is explicit and retains the original base revision and write set until final Git-diff reconciliation.

- The release-readiness changelog check is local and read-only; it adds no execution resource, credential, or tag-writing capability.

Sparse delegation does not relax isolation requirements: each justified auxiliary task retains its declared read/write scope and required execution isolation; primary preference does not select an isolation provider.
