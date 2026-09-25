# Secret Handling and Credential Safety

Use whenever implementation, testing, deployment, external API integration or debugging needs credentials, keys, tokens, certificates, passwords or other sensitive configuration.

## Core rule

Secret values are runtime inputs, not source code, prompts, Project Intelligence or review artifacts.

Never persist a real secret into source code, committed config, Agent instructions, Project Intelligence, generated HTML, logs, screenshots, test snapshots, examples, fixtures or review artifacts.

## Acquisition priority

Prefer:

~~~text
managed/workload identity or connected provider
→ approved secret manager / vault
→ protected CI/CD secret store
→ OS/runtime credential store
→ process environment injected at runtime
→ local uncommitted secret file only when necessary
~~~

Do not ask the user to paste a secret into chat when a connector, credential store, environment variable or secret manager can satisfy the task.

## Code contract

Application code consumes a secret reference/config key, not an embedded value.

~~~text
code
→ configuration name/reference
→ runtime secret provider
→ secret value
~~~

Templates/examples use placeholders only.

## Process safety

- avoid secret values in command-line arguments when practical;
- prefer provider-native auth, stdin, file descriptors, protected temporary files or runtime injection;
- use least-privilege credentials with the shortest practical lifetime;
- never print environment dumps;
- redact Authorization/Cookie/API-key headers, signed URLs and token query parameters;
- do not enable verbose HTTP/debug logging when it may expose credentials;
- delete temporary secret material when no longer needed.

## Local development

If a local secret file is required:

- exclude it from version control;
- restrict file permissions;
- commit only placeholder/example keys;
- never copy real values into tests or documentation.

## API / external integration

Before an authenticated call:

1. identify minimum credential scope;
2. identify approved secure acquisition source;
3. verify the runtime reads the secret indirectly;
4. verify logs/errors redact sensitive data;
5. only then execute the authenticated integration.

If the requested capability explicitly requires a credential for that operation and no credential-free path exists, mark that specific operation BLOCKED.

If the credential is declared optional, use the capability's truthful non-PASS state (for example `SKIPPED_NOT_CONFIGURED`, `ANALYSIS_PENDING`, or `TRIAL_PENDING`) and do not block unrelated baseline validation or release. Do not solve missing credentials by hard-coding them.

## Secret leakage review

Security review inspects applicable changed source/config, generated artifacts, fixtures/snapshots, logs, deployment manifests, CI config and Project Intelligence/HTML.

Use deterministic secret scanning for applicable security review. Scanner output is evidence, not proof of absence.

Every Remote Git publication candidate MUST pass the built-in, credential-free scanner in strict publication mode. The scan covers the exact committed final tree and every commit in `base..head`, so deleting a value in a later commit does not erase its earlier exposure from the candidate history. No scan, a scanner error, invalid policy, expired exception, incomplete history or unreadable candidate text is BLOCKED.

The canonical policy is `config/secret-scan.yaml`. Strict publication mode ignores no inline bypass markers. Exceptions require a centrally reviewed exact path, detector and SHA-256 fingerprint, a reason and an expiry; policy stores no secret value. Lockfiles disable only the generic assignment detector; provider-specific tokens, private keys and credential-bearing URLs remain detectable. External scanners such as Gitleaks or GitGuardian are optional defense-in-depth and are not baseline credentials or runtime requirements.

The Integration Gate binds PASS evidence to the exact base/head, changed-file set, policy hash and scanner hash. A changed candidate, policy or scanner requires a new scan. Reports contain only finding locations, detector names and truncated fingerprints, never secret values. The scan adds no approval authority: the existing Human-controlled Git Publish Approval remains in force.

Review both accidental secret values and unsafe handling patterns.

## Exposure response

If a real secret is exposed:

1. stop propagating/quoting it;
2. redact future output;
3. identify affected provider/scope without repeating the value;
4. rotate/revoke through the proper provider when required;
5. remove the value from current artifacts/source;
6. assess history/log/cache exposure;
7. re-run security checks;
8. record only redacted evidence.

Deleting a committed secret alone does not make the credential safe.

For SAL 3–4 or production credentials, unresolved active exposure blocks release.

## Protected-main provider verification

A provider credential verification workflow MUST NOT expose a provider secret to unmerged pull-request code.

For Gemini live-provider verification:

- `GEMINI_API_KEY` may be consumed only from a protected GitHub Actions secret context after the verification infrastructure is trusted;
- the value must not be written to workspace `.env`, extension settings, logs, canonical event sink, artifacts or committed evidence;
- missing `GEMINI_API_KEY` records `SKIPPED_NOT_CONFIGURED`; it cannot be interpreted as PASS and does not block unrelated baseline/release validation;
- provider-session verification grants no runtime enforcement, remediation, merge, release or publication authority.



## External Credential Dependency Guard

AIPS maintains `config/external-credentials.yaml` as the deterministic registry for external Agent/provider credentials.

`scripts/external_credential_guard.py` scans executable/configuration surfaces and blocks validation when:

- an external credential is referenced but not declared;
- a new consumer is not allowlisted;
- an external credential becomes required for baseline or release;
- a credential-consuming workflow exposes the secret to pull-request code;
- a credential-free default path exposes a secret outside its explicit credential-dependent branch.

The guard reads source/configuration only. It does not read secret values, create credentials, contact providers, or grant protected authority.
