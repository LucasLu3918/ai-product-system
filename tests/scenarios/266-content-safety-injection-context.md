# Scenario 266 — Content Safety Injection Context and Recovery

The deterministic scanner does not classify ordinary JavaScript data references as injection. Versioned override and exfiltration rules still block strong malicious samples; agent-directed execution has an independent rule ID; ambiguous imperative language produces `REVIEW` and the commit guard denies unresolved findings.

For staged commits and publication-candidate diffs, Secret and PII scans inspect complete staged blobs or the complete diff. Injection findings must overlap added lines and carry source path, line, rule ID, and stable finding fingerprint. Removed or unchanged suspicious text does not block an unrelated edit. Comments and strings remain eligible for strong-signal detection; whole file types are never allowlisted.

Email rule `pii.email.v2` does not report the exact ASCII `git` userinfo of an scp-like or `ssh://` Git remote, including quoted prefix literals and template paths. Prose after a colon, personal remote users, `https` userinfo, case variants, confusables and any address adjacent to a remote remain blocked. Redaction uses the same predicate, a secret in the same content still blocks, and `pii.*` exception records are rejected. A hex-encoded corpus compares v1 and v2 outcomes.

Exact exceptions require a known injection rule, repository-relative path, matching fingerprint and sink, future expiry, approver, and approval reference. Wrong-scope, expired, malformed, Secret, PII, unsupported-binary and scanner-failure cases remain denied.

`aips safety diagnose commit` and the native Hook share the same scanner. Structured recovery includes the reason code, blocking phase, safe evidence, next step, and whether human review is required. It excludes matched content and does not authorize commit or publication. The diagnostic leaves HEAD and the Git index unchanged.

`tests/test_content_safety.py` and `tests/test_safety_diagnostics.py` provide deterministic benign/malicious corpus, staged and publication diff-range, exception, privacy, Hook and read-only lifecycle evidence. A fixed corpus comparison records old/new false-positive and true-positive outcomes before the policy is enabled.
