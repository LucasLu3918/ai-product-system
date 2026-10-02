# Deterministic Scheduler

Use after planning when one approved change is decomposed into multiple bounded tasks that may execute independently.

The Scheduler is deterministic code, not a Role, Agent, approval gate or architecture decision-maker.

## Separation of responsibilities

~~~text
Human-approved scope
→ Planner / Orchestrator reasons once
→ Structured Task Graph
→ deterministic Scheduler
→ bounded writer workspaces
~~~

The Planner may define objectives, dependencies, Change Boundaries, read/write sets, role/skill hints and validation profiles. The Scheduler may only decide readiness, ordering, parallel slots and boundary locks from that declared graph/state.

It must not invent tasks, expand scope, resolve requirement/architecture conflicts, approve risk, merge, release or reinterpret a failed dependency.

## Task Graph contract

Use `templates/automation/TASK_GRAPH.yaml` and `orchestration/schemas/task-graph.yaml`.

Required deterministic inputs are:

- `plan_id`;
- `base_revision`;
- `max_parallel`;
- unique task IDs;
- explicit dependencies;
- canonical Change Boundary IDs;
- stable `order` plus task ID tie-breaker.

Read/write sets are declared evidence for implementation and reconciliation. Change Boundary IDs are the scheduler lock authority.

## State model

Input task states are compact persisted facts:

~~~text
PENDING | RUNNING | COMPLETE | FAILED | BLOCKED | STALE | CANCELLED
~~~

Readiness is derived, not stored as model judgment.

- all dependencies COMPLETE → eligible;
- dependency still PENDING/RUNNING → wait;
- dependency FAILED/BLOCKED/STALE/CANCELLED → downstream blocked;
- active or selected overlapping Change Boundary → defer;
- `max_parallel` reached → defer.

The same Task Graph + state must produce the same dispatch decision and fingerprints.

## Boundary locks

A boundary conflicts when it is equal to, an ancestor of, or a descendant of another active boundary. This operationalizes the existing single-writer rule across parallel worktrees.

Parallel writers are allowed only for non-overlapping approved boundaries. Isolation never creates permission to write outside a boundary.

## Resume

The scheduler is stateless between invocations. Durable workflow state remains owned by existing Run State / Workspace State facilities. A resumed run supplies the current persisted task statuses and current project revision; stale revision/scope routes back through normal refresh/replanning rather than being guessed around.

## CLI

Run-state and telemetry event producers share the same locked append stream. Concurrent writes allocate sequence numbers inside the lock and fsync each appended record before returning; the dashboard remains a read-only projection.

The local validation preparation entry reports the selected venv alongside actionable Python, dependency, writable-temp, localhost and browser diagnostics before exact-candidate Gate execution. Publication preview checks working-tree documentation placement and matrix binding before commit; matrix synchronization resolves an explicit or current checkout before writing.

Lifecycle subprocess 應以目前驗證器的 `sys.executable` 啟動，確保子程序沿用相同 Python runtime 與相依套件環境。

Publication preview includes uncommitted paths; use its `required_by` mapping to identify the sync or placement rule behind each documentation requirement before entering the exact-candidate Integration Gate.

`aips run list`, `aips run inspect` and `aips run dashboard` consume the same read-only run projection. They observe scheduler-related state but do not alter scheduler authority.

~~~bash
aips scheduler --graph TASK_GRAPH.yaml --state STATE.yaml --format yaml
~~~

Direct helper:

~~~bash
python scripts/deterministic_scheduler.py --graph TASK_GRAPH.yaml --state STATE.yaml
~~~

CI 會在合併前以 exact candidate 執行 Integration Gate；required aggregate 只有在 Gate 成功時才可通過。
Gate 的 mandatory candidate secret scan 會檢查 final tree 與 `base..head` 全部 commit，並在昂貴驗證依賴安裝前先行執行；它不改變既有 required aggregate 或 Human merge authority。
CI 在這項掃描通過後以相同 base/head 執行 repository preflight，再安裝完整依賴與 Chromium；任一步失敗都阻止昂貴的 lifecycle，但不取代後續 Integration Gate。

本機 `aips publish preflight` 與 CI 都先經過 `scripts/publish_preflight.py`，共用 base/head、change class、canonical matrix 與文件 diff base，再委派既有 Integration Gate。此入口只消除解析差異，不把 publication 或 merge authority 交給 Scheduler。

The same workflow uses a committed npm lockfile, `npm ci`, and lockfile-keyed dependency caching for the VitePress docs build. Publication Preflight may report repository-enabled merge methods as operator guidance; the Scheduler and preflight do not select or execute a merge.

Preflight 也驗證候選 checkout 與 Core Matrix changed-files hash；若工作樹 dirty、HEAD 不符或 browser smoke probe 失敗，應在 lifecycle 前回報明確的 `BLOCKED`／`ENVIRONMENT_BLOCKED` 原因。

提交前的 publication preview 亦檢查 Matrix 狀態、blockers 與實際差異核對；這些條件與正式 Gate 共用判定，避免預覽宣稱可進 Gate 卻被同一矩陣擋下。

Output includes graph/state/decision SHA-256 fingerprints for reproducibility.

CI integration evidence is written to the runner temporary directory and uploaded after validation. Scheduler and repository checks therefore inspect the unchanged checkout revision instead of treating generated reports as dirty inputs.
Repository validation timing is written to the same runner temporary area and uploaded separately; the report contains check names, statuses and durations only. This does not alter deterministic dispatch, the candidate revision or the required aggregate.
Publication Preflight lifecycle evidence stubs the Python module probe before asserting loopback/browser blockers; this keeps environment diagnosis deterministic without changing Gate behavior.

## Failure behavior

The Integration Gate never executes a generator configured in an Implementation Profile. For Phase 4 changes it runs only the isolated fake-generator lifecycle fixture; project generator execution remains an explicit local `--execute` action.

The OpenAPI contract-test action is explicit argv evidence attached to an implementation task; it does not grant scheduler authority or bypass the task write boundary. A missing command, timeout, nonzero exit or incomplete JUnit operation coverage remains non-PASS.

Phase 3 command evidence is likewise collected only as an explicitly selected project action. The Scheduler may order that action before an Integration Gate task, while the Gate reads its current-run report and performs no command execution from the candidate Implementation Profile. An expired or incomplete report leaves the dependent task blocked.

Publication Preflight checks runtime prerequisites before launching the expensive Integration Gate lifecycle. `ENVIRONMENT_BLOCKED` identifies missing Python/Ruff, loopback or browser capability; it is an environment result, not a Scheduler or product test failure.

Optional observed-stage recording reports `DEGRADED` when a run destination is absent or event writing fails. This observation is evidence only and does not alter the command's primary status.

Trajectory Quality Gate 可記錄 scheduler/tool execution 的 observable events，但不改變 scheduler 的 authority。必要 invariant 或 authorization 失敗應形成 evidence，並由上層 Integration/Publish Gate 依 policy 處理。

若 localhost bind 或 browser prerequisite 不可用，publication preflight 會在昂貴 lifecycle 前回報 `ENVIRONMENT_BLOCKED`；這是執行環境阻擋，不得記錄為產品測試失敗。

Invalid graph, unknown dependency, cycle, invalid state or plan mismatch is `SCHEDULER BLOCKED`.

Publication preview performs the bounded content-safety and configured Git identity checks before scheduling repository lifecycle validation; an unscannable candidate or disallowed identity is a deterministic preflight block.

GitHub Actions workflow concurrency is a separate CI scheduling boundary: the validate group includes the pull request action so label updates do not cancel `opened` validation. Only superseded `synchronize` revisions and earlier main push runs are cancellable; this does not alter Scheduler task ownership or the required `repository` check.

When the Execution Profile requires sandbox isolation, Scheduler dispatch must preserve its risk, minimum-isolation and data-class inputs and stop on `UNSUPPORTED`/`BLOCKED`. Worktree or shared execution is not a fallback for a task whose minimum isolation is sandbox. The E2B candidate remains disabled until its task adapter and data-transfer scope are approved.

The Scheduler never falls back to LLM coordination to make a blocked graph look executable.

## Read-only declaration and fail-closed boundary

Task Graphs now include explicit `read_only` intent.

- default/omitted `read_only` means the task may write and therefore MUST declare a non-empty Change Boundary;
- only `read_only: true` may omit Change Boundary;
- a read-only task with a non-empty `write_set` or explicitly writable isolation is invalid.

This rule prevents missing planning metadata from becoming an unlocked writer. The Scheduler blocks the graph instead of assuming an empty boundary is safe.

### Execution ownership and completion

`aips run owner claim` binds a scheduler-dispatched task to one runtime execution, active AIPS worktree, Change Boundary, write/read sets, dependencies and renewable lease. Claims serialize against shared scheduler state; deterministic dispatch remains authoritative and overlapping active boundaries cannot be claimed concurrently.

Leases move through `ACTIVE`, `STALE`, `ORPHANED`, `RECOVERY_REQUIRED`, `BLOCKED` and `RELEASED`. Expiry does not reassign a task. Dirty stale/orphaned work requires an explicit `recover` command, reason and `--accept-dirty` acknowledgement before another execution can resume it. Missing worktrees remain recovery-required.

Final reconciliation compares the Git diff from the lease base revision, including staged, unstaged and untracked files, against the task write set. Out-of-scope changes set the task to `BLOCKED`; only `ActualDiff ⊆ WriteSet ⊆ ChangeBoundary` can mark it complete. A rename is checked as its old and new paths. Ownership events contain task/execution IDs and bounded path evidence, never file contents.

Task-derived Resource Authorization is default deny outside the write set. `aips run owner authorize` emits `ADVISORY_ALLOW` only for declared paths and explicitly reports `enforced: false`; outside paths or inactive/wrong owners are `DENY`. The lease does not claim to intercept writes. A runtime is reported `TOOL_GUARDED` only after a verified native write guard is connected. Ownership is an optional additive run record, so Task Graph v1 and legacy checkpoints remain valid.

### Review task contract

An optional task `review` block declares `mode: SELF_CHECK | INDEPENDENT_REVIEW`, `review_of_task`, `required`, `context_inheritance`, and `allowed_context_classes`. A reviewer task is always `read_only: true`, has an empty `write_set`, and depends on the task it reviews. Independent review uses only allowlisted canonical evidence classes and requires `context_inheritance: none`.

Execution IDs and runtime attestation are produced by the execution runtime and recorded in task state; they are not guessed from Role, model, prompt, or task labels. On completion, the Scheduler validates structured evidence. Same execution becomes `FAILED`; absent/unverifiable runtime evidence becomes `UNVERIFIED`; packet/candidate drift becomes `STALE`. A required review that does not meet its declared mode is not treated as COMPLETE for downstream dispatch. The Integration Gate separately checks the report against the exact candidate.

## Validation de-duplication boundary


The repository validator may skip the focused Scheduler/Integration Gate lifecycle only when `AIPS_PROFILE_LIFECYCLE_ALREADY_EXECUTED=1` is injected by the deterministic Validation Profile after those checks already ran. Standalone repository validation must execute the lifecycle evidence normally.

## Runtime resource requests

Task Graph isolation metadata may declare bounded TCP port needs:

~~~yaml
isolation:
  mode: worktree
  required: true
  runtime:
    ports:
      - id: dev
        protocol: tcp
        preferred: 3000
        expose_as: [PORT]
~~~

The Scheduler validates this structure and includes runtime requirements only for tasks in the current deterministic `dispatch` as `runtime_requests`. It does **not** select host ports or probe sockets. The Orchestrator hands each dispatched request to the existing Execution Isolation lifecycle, where the repository-scoped lease registry and host availability checks live.

Only `tcp` is supported in v0.51. Port IDs must be stable resource IDs, `preferred` is optional and non-authoritative, and `expose_as` accepts environment-variable names only.
## Runtime Content Safety Boundary

Content safety decisions used by deterministic execution and publication preflight must be provider-neutral and reproducible. Optional semantic classifiers may emit advisory signals only and cannot be the sole release decision.

Runtime action authorization is evaluated at the native tool boundary by Runtime Policy Enforcement; task dispatch metadata does not grant action approval or network-egress isolation.
