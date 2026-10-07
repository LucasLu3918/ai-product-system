# Parallel Run Dashboard

The Parallel Run Dashboard is a read-only Human Operations View over existing AIPS durable run state. It is not a new state source, control plane, approval surface or database.

## Contract

The read-only run projection keeps its canonical digest facade and stable bytes over the shared helper; the dashboard remains a projection with no independent state or authority.

`scripts/run_projection.py` combines `CHECKPOINT.yaml`, append-only `EVENTS.jsonl`, workspace identity/fingerprint, optional execution/gate metadata and task ownership lease state into one normalized snapshot. CLI and browser consumers use this same projection.

The default scope is `repository_id`, so runs in the main workspace and parallel worktrees are visible together. A missing or changed workspace is reported as `WORKSPACE_MISSING` or `STALE`; the projection never infers that `ACTIVE` means the Agent process is live.

Checkpoint v3 metadata is optional and backward compatible with v1/v2. `execution` and `gate` fields are observability metadata only. Optional `TASK_OWNERSHIP.yaml` exposes task, owner, boundary, worktree, dirty paths, dependencies, heartbeat, recovery status and enforcement capability. Projection remains read-only and never promotes an expired lease to a new owner.

## CLI and local API

```bash
aips run list --project .
aips run inspect --project . --run-id <run-id>
aips run dashboard --project .
aips run dashboard --project . --open
aips run owner status --project . --run-id <run-id> --format yaml
```

The server binds only to `127.0.0.1` and exposes:

```text
GET /api/v1/runs
GET /healthz
```

The browser polls the API. There are no mutation, approval, merge, publish, retry or cancellation endpoints. API output is a whitelist and excludes prompts, reasoning, raw Agent output, secrets, environments and raw workspace paths.

## Failure and security behavior

- A truncated final JSONL line is ignored; valid prior events remain usable.
- The server uses `Cache-Control: no-store` and no CORS allowance.
- Event and ownership data are bounded; HTML interpolation escapes untrusted projected fields.
- Dashboard startup never writes a checkpoint or event.
- Dashboard shutdown cannot affect Scheduler, Agent, Gate, Resume or Git publication.
- Missing ownership data in legacy checkpoints projects as `UNASSIGNED` without migration or writes.
