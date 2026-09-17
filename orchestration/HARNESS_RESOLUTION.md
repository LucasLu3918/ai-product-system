# Harness Resolution

Use this to deterministically resolve runtime/project context before reasoning.

## Two levels

### Session / environment resolution

~~~bash
aips harness resolve --cwd "$PWD"
~~~

Resolves runtime, project root, project mode and native instruction pointers.

### Turn Context

~~~bash
aips intelligence context --runtime <runtime> --project <path> --prompt "<current request>"
~~~

Resolves a compact TURN_CONTEXT_MANIFEST.

Do not use Turn Context to perform repository-wide scans.

## Project modes

### EPHEMERAL

- no project-local `.ai/` is created;
- current tasks may use AIPS normally;
- reusable Project Intelligence may persist externally under `~/.config/aips/projects/<project-id>/intelligence/`;
- project source remains unchanged.

### ATTACHED

- explicit `aips attach`;
- persistent workspace lives in project `.ai/`;
- canonical Project Intelligence lives in `.ai/intelligence/`.

## Runtime capability

Installation status and capability are different.

- TURN_NATIVE — native per-turn hook injection.
- CONTEXT_ALWAYS — persistent instructions require per-turn AIPS resolution.
- SESSION_ONLY — bootstrap at session only.
- MANUAL — explicit action required.
- UNSUPPORTED — no safe integration.

## Instruction composition

Resolve without replacing:

~~~text
Platform / Safety
→ AIPS Constitution / Governance
→ Current explicit user decision
→ Runtime-native instructions
→ nearest project instructions
→ ADR / authoritative contracts / official docs
→ PROJECT_OVERRIDES
→ Project Intelligence
→ project-local Skills
→ AIPS Skills
→ inference
~~~

Runtime-mandated precedence remains authoritative for that Runtime.

The Turn Context manifest exposes this as structured `resolution.instruction_precedence` and `resolution.instruction_sources`. AIPS does not guess semantic contradictions with string heuristics. Material conflicts identified by the Agent or an approved project override are recorded structurally in Project Intelligence / `PROJECT_OVERRIDES.yaml`, surfaced as `resolution.instruction_conflicts`, and an unresolved material conflict fails closed for mutation while remaining visible for read-only work. Resolving a conflict records the decision; it does not silently rewrite the underlying permanent instruction source.

## Runtime-aware deduplication

SOURCE_REGISTRY distinguishes:

- authoritative storage source;
- scope;
- hash/freshness;
- which runtimes auto-load the source.

Example: Codex may auto-load AGENTS.md while Claude does not. Therefore "do not duplicate storage" does not mean "never load it for another runtime".

## Failure policy

- general/read-only request: Harness/Intelligence problems fail soft when safe;
- existing-project mutation: missing required instructions/Intelligence/Impact context fails closed for the edit until resolved.
