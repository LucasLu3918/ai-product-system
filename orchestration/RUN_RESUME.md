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
- project revision;
- updated timestamp.

Do not persist chat transcripts, prompts, private chain-of-thought, credentials or unnecessary sensitive payloads.

## Event contract

EVENTS.jsonl is append-only structured evidence. Each event contains sequence, timestamp, event name, status and optional artifact/evidence references.

Free-form raw prompt/model reasoning is prohibited.

## Resume

~~~text
load checkpoint
→ compare current project revision
→ same revision?
   ├─ yes → CURRENT → continue from recorded step
   └─ no  → STALE → refresh/revalidate affected evidence before continuation
~~~

Resume status does not bypass Requirement, Change Impact, Approval, Security, Test, Review or Release gates.

## Checkpoint timing

Checkpoint after material transitions such as:
- approved plan/core/system direction;
- implementation phase completion;
- validation/review completion;
- blocker/wait state;
- LOCAL_COMPLETE / release candidate transitions.

Avoid checkpointing every trivial command.
