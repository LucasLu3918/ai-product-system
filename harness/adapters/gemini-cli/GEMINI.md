# AIPS Global Turn Harness

This extension provides an AIPS BeforeAgent hook. Each user prompt receives compact current Turn Context before planning.

Use Project Intelligence pointers progressively; do not rescan the whole repository each turn. Existing-project mutation requires Intelligence initialization/refresh and Change Impact before editing.

## Optional AfterTool observable-event Trial hook

The extension also registers `aips-observable-event-capture` for `read_file|write_file|replace` AfterTool events.

It is **disabled by default**. Enable only for bounded verification with:

~~~bash
export AIPS_OBSERVABLE_EVENT_CAPTURE=1
export AIPS_OBSERVABLE_EVENT_CAPTURE_SINK=/tmp/aips-gemini-events.jsonl
~~~

Only canonical metadata is written to the explicit temporary sink. `tool_input`, `tool_response`, prompt/response text, private reasoning and secret values are never persisted by the capture hook.

The hook is **non-enforcing**, not asynchronous: it always returns `decision=allow`, so it does not deny or rewrite the tool result, but Gemini CLI waits synchronously for the AfterTool command to finish. The Trial therefore records `synchronous_hook=true` and `latency_path=synchronous`; `critical_path=false` means only that capture is not an authorization/result-enforcement gate. When capture is disabled, the shell wrapper returns allow directly without starting Python. It has no remediation authority and does not claim `live_capture_verified=true` until a real Gemini CLI runtime execution is separately verified.

## Verified runtime scope

Scenario 143 verifies the actual installed Gemini CLI v0.60.0 executable, extension loader, file-tool executor and this extension's AfterTool hook on an exact AIPS candidate.

The model side is intentionally deterministic: Gemini CLI is invoked with its official `--fake-responses` testing interface. Therefore the verified statement is narrow:

- `live_runtime_execution_verified=true`;
- `live_capture_verified=true` for `read_file|write_file|replace`;
- `provider_model_api_exercised=false`;
- `provider_model_execution_verified=false`.

This does not make capture default-on and does not change synchronous latency, authorization, result-flow or remediation semantics.

