# Scenario 145 — External Credential Dependency Guard

AIPS must prevent external Agent/provider API keys from silently becoming platform or release prerequisites.

Expected:

- deterministically scan workflow/config/script surfaces for external credential references;
- every discovered external credential is declared in `config/external-credentials.yaml`;
- every discovered consumer is explicitly allowlisted;
- `GEMINI_API_KEY` and `OPENAI_API_KEY` remain optional;
- no declared external credential is required for baseline AIPS operation or release;
- undeclared credential references fail validation;
- external credentials must not be exposed to `pull_request` or `pull_request_target` workflow code;
- the Retrieval semantic Trial defaults to the credential-free local path and injects `OPENAI_API_KEY` only in the explicit `remote` step;
- missing optional credentials retain truthful non-PASS states and do not authorize fallback authentication;
- the guard reads source/configuration only and never reads secret values or calls a provider;
- PASS grants no Human approval, merge, release, publication, credential creation, enforcement, or remediation authority.
