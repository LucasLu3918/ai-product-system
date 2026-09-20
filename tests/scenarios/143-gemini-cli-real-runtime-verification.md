# Scenario 143 — Gemini CLI Exact-Candidate Real-Runtime Verification

After the v0.33.0 implementation Trial, AIPS verifies the actual Gemini CLI runtime path without requiring or fabricating a live provider credential.

Expected:

- pin official Gemini CLI version 0.60.0;
- select `gemini-2.5-flash` explicitly so this capture Trial does not consume fake responses in the unrelated auto model-router path;
- execute the bundled real CLI binary in GitHub Actions;
- use Gemini CLI's official `--fake-responses` test interface only for deterministic model output;
- satisfy Gemini CLI's mandatory headless auth-type selection with `GOOGLE_GENAI_USE_GCA=true` only; provide no API key/OAuth credential, and record `auth_type_selector_only=true`;
- link the real AIPS Gemini extension through Gemini CLI's extension discovery path;
- enable `experimental.extensionConfig` and inject the non-secret capture controls through the isolated workspace `.env`, matching Gemini CLI's official extension-settings path;
- execute real built-in `read_file`, `write_file`, and `replace` tools against an isolated temporary workspace;
- observe the real `AfterTool` hook writing canonical metadata;
- verify 3 / 3 expected events with zero unexpected loss;
- verify the write and replace tools actually mutate the workspace;
- verify canonical event persistence contains no tool payload, file content, private reasoning or secret values;
- verify disabled capture produces no sink;
- bind the workflow to the exact pull-request head SHA;
- report `live_runtime_execution_verified=true` and runtime-specific `live_capture_verified=true` only if the exact-head workflow succeeds;
- separately report `live_provider_session_verified=false` and `provider_model_execution_verified=false` because fake model responses replace provider inference;
- preserve `runtime_enforced=false`, synchronous-hook latency truth, no remediation, no publication/merge/release authority;
- the next gate, if desired, is a separately authorized live-provider-session verification and must not be inferred from this Trial.
