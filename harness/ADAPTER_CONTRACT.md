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

Where a verified native pre-tool hook is installed, it may call the provider-neutral Runtime Policy Evaluator using a trusted normalized action envelope. Missing/invalid policy or required action context fails closed for recognized protected actions. A hook's `TOOL_GUARDED` capability does not imply shell, child-process or network isolation; high-risk egress separately requires verified sandbox/network evidence.

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

## MCP access-plane relationship

MCP interoperability is parallel to this Runtime Adapter contract.

- MCP provides portable AIPS Resources / Prompts / deterministic Tools to compatible hosts.
- A runtime-native Adapter is still required when AIPS needs verified per-turn injection, pre-tool interception or stronger runtime enforcement.
- Never promote MCP-only access from ADVISORY to TOOL_GUARDED merely because the client can call AIPS tools.
- Adapters and MCP read the same canonical Role / Skill / orchestration sources; neither may duplicate those bodies.
