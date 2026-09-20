# Scenario 142 — Codex PostToolUse Live-Capture Implementation Trial

After v0.32.0 adopts the observable-event capture design direction, the Human authorizes one bounded runtime-specific implementation Trial.

Selected runtime: **Codex CLI**.

Expected:

- current-main v0.32.0 evidence is fresh before the Trial Decision is recorded;
- Codex is selected because the official runtime exposes a native `PostToolUse` command hook that runs after supported tool output and supports async execution;
- AIPS composes only its namespaced `PostToolUse` hook into `~/.codex/hooks.json`, preserving unrelated user hooks;
- the hook matcher is limited to `apply_patch|Edit|Write`, while the actual hook input must report canonical `tool_name=apply_patch`;
- the handler is async, bounded and outside the critical path;
- installation remains disabled by default when no explicit capture config enables it;
- AIPS does not bypass Codex hook trust review and does not claim `hook_trust_verified=true`;
- the handler never persists `tool_input`, `tool_response`, session id, turn id, prompt/response text, private reasoning, chain-of-thought or secret-like values;
- successful/failed structured apply-patch outcomes can be normalized to canonical observable-event metadata;
- unresolved outcomes, sensitive payloads, unsupported tools and a full bounded buffer degrade/drop evidence rather than blocking the completed tool call;
- concurrent capture remains bounded;
- lifecycle evidence measures hook-processing p95 under a conservative 250 ms CI threshold;
- install/uninstall is reversible and modified AIPS hook state is preserved as a conflict rather than silently removed;
- `hook_contract_verified=true` is allowed, but `live_runtime_exercised=false` and `live_capture_verified=false` remain required because repository CI does not launch a real trusted Codex session;
- PASS stops at `HUMAN_REVIEW_RUNTIME_SMOKE_TEST`; production-wide enablement, runtime enforcement, semantic intent governance and automatic remediation remain out of scope.
