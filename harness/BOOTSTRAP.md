# AIPS Global Harness Bootstrap

AIPS is installed as a cross-agent software-engineering harness.

Keep this bootstrap small. Do not preload the entire AIPS repository.

## On every session

For ordinary conversation that does not involve product/project/software work, continue normally.

Before product/project/software planning or implementation:

1. resolve the active harness and project with `aips harness resolve`;
2. load the returned AIPS bootstrap/system pointers;
3. preserve runtime-native and project-local instructions;
4. load only the AIPS protocols, Project Knowledge topics, Roles and Skills required by the current task;
5. use AIPS governance/planning/review/completion rules for applicable engineering work;
6. never overwrite user-owned Agent instructions, skills or configuration merely to make AIPS easier to use.

## Project modes

- **EPHEMERAL** — AIPS may guide the current task, but must not create `.ai/` or persistent Project Knowledge automatically.
- **ATTACHED** — the user explicitly ran `aips attach`; AIPS may use/persist the project `.ai/` workspace.

## Instruction composition

Resolve, rather than replace:

- external platform/safety instructions;
- AIPS governance;
- current user decision;
- runtime-native instructions;
- nearest project AGENTS / accepted ADR / contracts / official docs;
- current Project Knowledge;
- project-local skills;
- AIPS skills;
- generic inference.

When native runtime precedence differs, follow the runtime's mandatory precedence while surfacing material conflicts instead of silently discarding either source.

## Minimal context

The bootstrap points into AIPS; it is not a request to read all files.

Start with `AGENTS.md` and `SYSTEM.md` only when AIPS engineering orchestration is applicable.
