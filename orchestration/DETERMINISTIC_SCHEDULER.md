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

~~~bash
aips scheduler --graph TASK_GRAPH.yaml --state STATE.yaml --format yaml
~~~

Direct helper:

~~~bash
python scripts/deterministic_scheduler.py --graph TASK_GRAPH.yaml --state STATE.yaml
~~~

CI 會在合併前以 exact candidate 執行 Integration Gate；required aggregate 只有在 Gate 成功時才可通過。

本機 `aips publish preflight` 與 CI 都先經過 `scripts/publish_preflight.py`，共用 base/head、change class、canonical matrix 與文件 diff base，再委派既有 Integration Gate。此入口只消除解析差異，不把 publication 或 merge authority 交給 Scheduler。

Output includes graph/state/decision SHA-256 fingerprints for reproducibility.

CI integration evidence is written to the runner temporary directory and uploaded after validation. Scheduler and repository checks therefore inspect the unchanged checkout revision instead of treating generated reports as dirty inputs.

## Failure behavior

Trajectory Quality Gate 可記錄 scheduler/tool execution 的 observable events，但不改變 scheduler 的 authority。必要 invariant 或 authorization 失敗應形成 evidence，並由上層 Integration/Publish Gate 依 policy 處理。

若 localhost bind 或 browser prerequisite 不可用，publication preflight 會在昂貴 lifecycle 前回報 `ENVIRONMENT_BLOCKED`；這是執行環境阻擋，不得記錄為產品測試失敗。

Invalid graph, unknown dependency, cycle, invalid state or plan mismatch is `SCHEDULER BLOCKED`.

The Scheduler never falls back to LLM coordination to make a blocked graph look executable.

## Read-only declaration and fail-closed boundary

Task Graphs now include explicit `read_only` intent.

- default/omitted `read_only` means the task may write and therefore MUST declare a non-empty Change Boundary;
- only `read_only: true` may omit Change Boundary;
- a read-only task with a non-empty `write_set` or explicitly writable isolation is invalid.

This rule prevents missing planning metadata from becoming an unlocked writer. The Scheduler blocks the graph instead of assuming an empty boundary is safe.

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
