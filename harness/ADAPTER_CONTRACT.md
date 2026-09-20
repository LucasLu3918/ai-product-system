# Runtime Adapter Contract

Every Adapter implements the same Turn Harness contract using the safest runtime-native mechanism.

## Capability states

- TURN_NATIVE — native per-prompt hook injects current context before planning.
- CONTEXT_ALWAYS — persistent instructions require current context resolution each turn; no deterministic native hook is claimed.
- SESSION_ONLY — AIPS is loaded only at session start.
- MANUAL — explicit action is required.
- UNSUPPORTED — no safe supported integration.

Installation status and context capability are separate.

## Governance enforcement capability

Report this independently from context capability:

- `ADVISORY` — instructions can request compliance but cannot deterministically intercept the protected tool call.
- `TOOL_GUARDED` — a verified runtime-native pre-tool hook can block configured protected operations.
- `ENFORCED` — the runtime/platform provides stronger non-bypassable enforcement for the declared operation class.
- `UNSUPPORTED` — no safe supported enforcement integration exists.

Never infer TOOL_GUARDED/ENFORCED from documentation alone; use installed adapter state. A guard may tighten policy but never create Human approval.

## Managed composition

When a shared instruction file is required, use an AIPS delimited managed block instead of owning the whole file. Existing user content remains unchanged outside the block.

Uninstall removes only an unchanged AIPS managed block. If the managed block was edited, preserve it and report conflict.

Structured settings integrations add/remove only an AIPS namespaced hook entry and preserve unrelated keys/hooks.

## Runtime targets

- Gemini CLI: extension + BeforeAgent → TURN_NATIVE.
- Claude Code: UserPromptSubmit → TURN_NATIVE when verifiable; managed CLAUDE memory is CONTEXT_ALWAYS fallback.
- Codex: managed global instruction composition → CONTEXT_ALWAYS; governance enforcement remains ADVISORY unless a native pre-tool guard is actually installed and verified.

## Adapter responsibilities

Adapters detect, integrate, verify and uninstall. They never implement Product/Security/Quality reasoning, preload the whole AIPS repository, replace user Skills, or hide capability limitations.

## Observable-event capture truth

Observable-event capture is reported separately from context capability and governance enforcement.

- `UNSUPPORTED` — no AIPS capture hook contract is installed/verified.
- `POST_EXECUTION_EVIDENCE` — a post-execution evidence hook contract exists; this does **not** mean it is enabled, trusted or live-verified.

Additional truth fields:

- `hook_contract_verified` — AIPS can deterministically compose and validate the runtime-native hook shape.
- `hook_trust_verified` — the runtime itself has accepted/trusted that exact non-managed hook definition.
- `live_capture_verified` — a real runtime session actually emitted evidence through the hook and passed the declared smoke-test contract.

Never infer later states from earlier ones. In particular, an installed Codex `PostToolUse` JSON entry is not proof that Codex trusted or executed it.

### Codex bounded capture

Scenario 142 composes an async, default-disabled `PostToolUse` hook for `apply_patch/Edit/Write`. It persists only sanitized canonical metadata and remains outside the critical path. Governance enforcement stays ADVISORY; anomaly evidence does not block or undo tool execution.

