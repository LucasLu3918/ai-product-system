---
id: security-testing
capability: security
estimated_context_cost: medium
---

# Security Testing

Convert the relevant threat model, abuse cases and security requirements into test evidence.

Use the least expensive suitable strategy, which may include authorization matrix tests, malformed input tests, replay/idempotency tests, concurrent/race-condition tests, rollback/failure tests, secret/logging checks, dependency/configuration scanning and integration/E2E security assertions.

SAL 3–4 security review must cite concrete evidence. Do not claim security solely from code inspection.


For credential-bearing changes, include applicable secret leakage checks across changed source/config, generated artifacts, fixtures/snapshots and logs. Test redaction/failure behavior without placing a real secret into fixtures.
