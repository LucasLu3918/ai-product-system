# Run Resume Protocol

Use for substantial workflows that may span turns, sessions or runtime restarts.

## Storage

All project modes:

~~~text
~/.config/aips/projects/<project-id>/runs/<run-id>/
├── CHECKPOINT.yaml
└── EVENTS.jsonl
~~~

Checkpoints and events always use the external user-state store. Legacy project-local `.ai/runs/` data is read only by explicit migration; new writes never target it.

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

Resume validates the external repository identity, revision and workspace fingerprint before reusing checkpoints; a mismatch requires refresh or revalidation.

~~~text
load checkpoint
→ resolve canonical repository_id / workspace_id
→ recompute workspace fingerprint
→ same workspace state?
   ├─ yes → CURRENT → continue from recorded step
   └─ no  → STALE → report revision/branch/dirty/identity drift → refresh/revalidate affected evidence
~~~

The fingerprint hashes product workspace state; legacy `.ai/` state is excluded and checkpoint writes occur outside the repository. Legacy v1 checkpoints fall back conservatively: a dirty workspace cannot be reported CURRENT solely because HEAD matches.

Resume status does not bypass Requirement, Change Impact, Approval, Security, Test, Review or Release gates.

Publication Secret Scan evidence is bound to the exact candidate and remains an external AIPS artifact pointer. Do not place raw scanner content or media payloads in checkpoints or EVENTS; resume must revalidate the candidate and current publication Gate evidence.

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
