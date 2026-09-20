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

## Real-runtime verification state

Scenario 143 verifies this adapter through pinned Gemini CLI v0.60.0 with the extension linked through the official extension mechanism.

The verifier executes real `read_file`, `write_file`, and `replace` tools. Model outputs are deterministic via Gemini CLI's official `--fake-responses` test interface, so no Gemini API credential is required.

When the exact-head verification workflow passes, this adapter may report runtime-specific `live_runtime_execution_verified=true` and `live_capture_verified=true`, while keeping `live_provider_session_verified=false` and `provider_model_execution_verified=false`.

The shell wrappers resolve their physical script directory before locating the AIPS repository. This is required because Gemini CLI loads linked extensions through a symlink under `~/.gemini/extensions`; resolving the symlink path lexically would point hook scripts at the temporary/user HOME instead of the AIPS checkout.

Scenario 143 also verifies the official extension-settings path: the isolated Gemini settings enable `experimental.extensionConfig`, and the non-sensitive capture controls are supplied from the temporary workspace `.env`. Parent-process environment inheritance is not treated as proof that hook settings propagate.

## Live provider-session gate

Provider/model inference is intentionally verified separately from the deterministic Scenario 143 runtime path.

The Human-approved next step is a bounded provider session using the protected GitHub Actions `GEMINI_API_KEY` secret. Until a trusted-main workflow executes that session successfully, this adapter MUST keep `live_provider_session_verified=false` and `provider_model_execution_verified=false`.

The provider secret must never be persisted into extension settings, workspace evidence, canonical events, logs, or committed result files.

