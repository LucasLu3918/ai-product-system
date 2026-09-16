# Turn-Aware Harness

AIPS uses one Harness Contract across runtimes, implemented with each runtime's safest native mechanism.

## Contract

Every user turn should be able to resolve:

- active AIPS version/protocol entry;
- runtime-native instructions;
- target project and project-native instructions;
- Project Intelligence location/status;
- task-relevant Intelligence topics;
- mutation impact requirements when applicable.

"Every turn resolves" does not mean "every turn scans the repository".

## Turn path latency budget

The synchronous turn path is intentionally small:

~~~text
resolve project identity
→ quick freshness check
→ load Intelligence index / Source Registry
→ classify task broadly
→ emit TURN_CONTEXT_MANIFEST
~~~

Heavy work such as initial bootstrap, broad targeted refresh, impact-graph rebuild and HTML regeneration happens outside the synchronous hook path.

## Capability states

Runtime capability is multidimensional:

- `TURN_NATIVE` — native per-prompt hook can inject current context before planning;
- `CONTEXT_ALWAYS` — persistent instructions tell the runtime to resolve context every turn, but no deterministic per-prompt hook exists;
- `SESSION_ONLY` — AIPS is loaded at session start only;
- `MANUAL` — explicit user/runtime action required;
- `UNSUPPORTED` — no safe supported integration.

Do not collapse these into a single AUTOMATIC label.

## Runtime targets

### Gemini CLI

Prefer extension + `BeforeAgent` for per-turn dynamic context. Use `BeforeTool` only for a narrowly justified mutation guard.

### Claude Code

Prefer a namespaced/user-safe hook mechanism capable of running on user prompt submission. Do not overwrite existing user memory files.

### Codex

Use persistent AIPS instructions plus Codex native instruction aggregation so every turn knows to resolve AIPS context. Do not claim native per-turn interception when the runtime does not provide it.

## Context budget

Load in this order:

1. minimal AIPS contract;
2. critical user/runtime/project instructions;
3. task-relevant Intelligence;
4. optional evidence on demand.

Prefer pointers/summaries over duplicating large authoritative documents.

## Failure policy

- general conversation: fail soft;
- existing-project mutation: missing required Harness/Project Intelligence context fails closed for the mutation, not for the entire conversation.
