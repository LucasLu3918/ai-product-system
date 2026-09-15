# Workspace State

Project state lives with the project, normally under `.ai/`.

Recommended minimum:

```text
.ai/
├── PROJECT.md
├── STATE.yaml
├── MANIFEST.yaml
├── decisions/
└── runs/
```

`STATE.yaml` is a compact resume point. Historical conversation is not required for continuation.

Persist only useful state: phase, active task, blockers, accepted decisions, artifact locations and last checkpoint. Do not turn state into an exhaustive transcript.
