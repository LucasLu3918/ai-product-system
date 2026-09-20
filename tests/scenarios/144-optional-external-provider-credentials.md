# Scenario 144 — Optional External Provider Credentials

AIPS operates normally without external Agent/provider credentials. Credential-dependent provider capabilities are optional enhancements and must not become implicit platform or release prerequisites.

Expected:

- external Agent/provider credentials are not required for baseline AIPS operation;
- credential-dependent provider verification is disabled unless the exact expected credential is explicitly configured;
- an absent `GEMINI_API_KEY` produces `SKIPPED_NOT_CONFIGURED`, not BLOCKED/FAIL/PASS;
- the absent-credential report sets `provider_verification_enabled=false` and `required_for_release=false`;
- `live_provider_session_verified=false` and `provider_model_execution_verified=false` remain truthful until real provider evidence exists;
- when the credential is absent, provider-specific install and live provider/model execution steps are skipped;
- the workflow remains protected-main/manual only and never exposes provider credentials to pull-request code;
- credential values are never persisted in committed evidence, canonical events, logs, or artifacts;
- no OAuth, Vertex AI credential path, GitHub OIDC / Workload Identity Federation, or other replacement login flow is enabled by default;
- existing credential-free Gemini CLI real-runtime/tool/AfterTool verification remains independent and available;
- missing optional provider credentials do not block unrelated validation, merge, or release;
- enabling any future external credential-dependent capability requires explicit configuration and must preserve Protected Human Authority.
