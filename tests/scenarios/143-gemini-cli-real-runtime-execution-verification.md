# Scenario 143 — Gemini CLI Real Runtime Execution Verification

Request: after the bounded Scenario 142 implementation Trial, the Human authorizes the recommended exact-candidate real Gemini CLI runtime verification.

Expected:

- install and pin the current approved Gemini CLI stable version `0.60.0` in CI;
- invoke the actual installed `gemini` binary rather than importing Gemini CLI internals or directly calling the AIPS hook;
- link/load the real AIPS Gemini extension;
- use Gemini CLI's official `--fake-responses` testing interface so no provider credential is required and provider/model API execution is not claimed;
- execute real Gemini CLI `read_file`, `write_file` and `replace` tool paths under `--approval-mode=yolo`;
- verify real file effects for write/replace;
- verify the extension's native `AfterTool` hook emits exactly three canonical metadata events;
- verify disabled-by-default behavior through a real CLI run with capture unset;
- persist no raw `tool_input`, `tool_response`, file contents, private reasoning or secret-like values;
- preserve `runtime_enforced=false`, non-enforcing synchronous-hook semantics and all protected authority=false;
- set `live_runtime_execution_verified=true` and `live_capture_verified=true` only for the narrow Gemini CLI v0.60.0 local binary/tool/hook scope;
- keep `provider_model_api_exercised=false`, `provider_model_execution_verified=false` and `network_model_call_verified=false`;
- require the real-runtime job through the existing `repository` compatibility aggregate for core/large PRs and protected-main pushes;
- do not expand to shell/MCP/network tools, provider-backed model execution, durable production persistence, semantic intent governance, automatic remediation, or another runtime.
