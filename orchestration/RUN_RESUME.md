# Run Resume Protocol

Use for substantial workflows that may span turns, sessions or runtime restarts.

## Storage

ATTACHED:

~~~text
.ai/runs/<run-id>/
├── CHECKPOINT.yaml
└── EVENTS.jsonl
~~~

EPHEMERAL:

~~~text
~/.config/aips/projects/<project-id>/runs/<run-id>/
├── CHECKPOINT.yaml
└── EVENTS.jsonl
~~~

EPHEMERAL must not create project-local .ai state.

## Checkpoint contract

Persist only compact execution state:

- run id and protocol;
- current step/status;
- completed steps;
- blockers/waiting-for;
- evidence/artifact pointers;
- repository/workspace identity;
- project revision + branch;
- dirty-state/workspace fingerprint;
- updated timestamp.

Do not persist chat transcripts, prompts, private chain-of-thought, credentials or unnecessary sensitive payloads.

## Event contract

EVENTS.jsonl is append-only structured evidence. Each event contains sequence, timestamp, event name, status and optional artifact/evidence references.

Free-form raw prompt/model reasoning is prohibited.

## Resume

~~~text
load checkpoint
→ resolve canonical repository_id / workspace_id
→ recompute workspace fingerprint
→ same workspace state?
   ├─ yes → CURRENT → continue from recorded step
   └─ no  → STALE → report revision/branch/dirty/identity drift → refresh/revalidate affected evidence
~~~

The fingerprint hashes product workspace state; AIPS-owned `.ai/` state is excluded so checkpoint writes do not invalidate themselves. Legacy v1 checkpoints fall back conservatively: a dirty workspace cannot be reported CURRENT solely because HEAD matches.

Resume status does not bypass Requirement, Change Impact, Approval, Security, Test, Review or Release gates.

## Dashboard boundary

The Parallel Run Dashboard is a read-only projection over this protocol. It may aggregate runs by `repository_id` across workspaces, but it must not become a second state source or state machine. Its API cannot approve, mutate, merge, publish, retry or cancel a run. `ACTIVE` remains the last-known workflow state; process liveness requires a separate future heartbeat/lease contract.

## Checkpoint timing

Checkpoint after material transitions such as:
- approved plan/core/system direction;
- implementation phase completion;
- validation/review completion;
- blocker/wait state;
- LOCAL_COMPLETE / release candidate transitions.

Avoid checkpointing every trivial command.
