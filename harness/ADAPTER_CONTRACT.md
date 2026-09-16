# Runtime Adapter Contract

Every Adapter implements the same Turn Harness contract using the safest runtime-native mechanism.

## Capability states

- TURN_NATIVE — native per-prompt hook injects current context before planning.
- CONTEXT_ALWAYS — persistent instructions require current context resolution each turn; no deterministic native hook is claimed.
- SESSION_ONLY — AIPS is loaded only at session start.
- MANUAL — explicit action is required.
- UNSUPPORTED — no safe supported integration.

Installation status and capability are separate.

## Managed composition

When a shared instruction file is required, use an AIPS delimited managed block instead of owning the whole file. Existing user content remains unchanged outside the block.

Uninstall removes only an unchanged AIPS managed block. If the managed block was edited, preserve it and report conflict.

Structured settings integrations add/remove only an AIPS namespaced hook entry and preserve unrelated keys/hooks.

## Runtime targets

- Gemini CLI: extension + BeforeAgent → TURN_NATIVE.
- Claude Code: UserPromptSubmit → TURN_NATIVE when verifiable; managed CLAUDE memory is CONTEXT_ALWAYS fallback.
- Codex: managed global instruction composition → CONTEXT_ALWAYS; do not claim native per-turn interception.

## Adapter responsibilities

Adapters detect, integrate, verify and uninstall. They never implement Product/Security/Quality reasoning, preload the whole AIPS repository, replace user Skills, or hide capability limitations.
