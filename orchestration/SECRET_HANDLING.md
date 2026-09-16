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

If credentials are unavailable, mark the operation BLOCKED. Do not solve missing credentials by hard-coding them.

## Secret leakage review

Security review inspects applicable changed source/config, generated artifacts, fixtures/snapshots, logs, deployment manifests, CI config and Project Intelligence/HTML.

Use deterministic secret scanning where practical. Scanner output is evidence, not proof of absence.

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
