# External Credential Dependency Guard

## Purpose

Keep AIPS baseline operation and release independent from external Agent/provider API keys.

The guard is deterministic. It audits source/configuration references only; it never reads secret values and never calls an external provider.

## Policy

- external Agent/provider credentials are optional capability inputs;
- no external credential may become required for baseline AIPS operation;
- no external credential may become required for release;
- every external credential reference on executable/configuration surfaces must be declared in `config/external-credentials.yaml`;
- undeclared credentials or undeclared consumers fail validation;
- workflows that consume external credentials must not expose them to `pull_request` / `pull_request_target` code;
- when a capability defaults to a credential-free path, its secret must be injected only into the explicit credential-dependent branch;
- missing optional credentials use the capability's declared non-PASS state such as `SKIPPED_NOT_CONFIGURED`, `ANALYSIS_PENDING`, or `TRIAL_PENDING`;
- missing optional credentials do not create merge/release authority and do not block unrelated baseline/release validation.

## Current registry

The current external Agent/provider credentials are:

- `GEMINI_API_KEY` — optional live Gemini provider-session verification only;
- `OPENAI_API_KEY` — optional Evolution semantic/trial paths and explicit remote Retrieval embedding Trial only.

Credential-free alternatives remain the default where defined: provider-neutral Evolution handoff, local Retrieval embedding Trial, and Gemini runtime verification with deterministic fake model responses.

## Execution

~~~bash
python scripts/external_credential_guard.py audit \
  --config config/external-credentials.yaml \
  --root .
~~~

A PASS is dependency-policy evidence only. It does not prove provider authentication, create credentials, or authorize protected operations.

## Authority

The guard grants no Human approval, merge, release, publication, credential creation, runtime enforcement, or automatic remediation authority.
