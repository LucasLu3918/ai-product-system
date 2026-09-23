# Parallel Run Dashboard

The Parallel Run Dashboard is a read-only Human Operations View over existing AIPS durable run state. It is not a new state source, control plane, approval surface or database.

## Contract

`scripts/run_projection.py` combines `CHECKPOINT.yaml`, append-only `EVENTS.jsonl`, workspace identity/fingerprint and optional execution/gate metadata into one normalized snapshot. CLI and browser consumers use this same projection.

The default scope is `repository_id`, so runs in the main workspace and parallel worktrees are visible together. A missing or changed workspace is reported as `WORKSPACE_MISSING` or `STALE`; the projection never infers that `ACTIVE` means the Agent process is live.

Checkpoint v3 metadata is optional and backward compatible with v1/v2. `execution` and `gate` fields are observability metadata only. They cannot grant approval or change canonical state.

## CLI and local API

```bash
aips run list --project .
aips run inspect --project . --run-id <run-id>
aips run dashboard --project .
aips run dashboard --project . --open
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
- Event text is bounded and rendered with `textContent`.
- Dashboard startup never writes a checkpoint or event.
- Dashboard shutdown cannot affect Scheduler, Agent, Gate, Resume or Git publication.
- A future heartbeat/lease model is intentionally outside v0.58.0.
