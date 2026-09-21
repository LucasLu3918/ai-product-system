# Scenario 158 — Verifiable Governance Audit Chain

A maintainer must be able to audit a high-assurance approval/security/release/deployment history later without trusting an Agent narrative.

Expected:
- governance events are canonicalized and chained by SHA-256;
- modifying or reordering a recorded event fails verification; interior deletion breaks continuity, while tail truncation is detected when the auditor supplies the previously anchored chain head/event count;
- optional HMAC-SHA256 authenticates events without persisting the secret;
- optional Ed25519 checkpoint verification uses a public key and detects a wrong key/signature;
- authenticated/signed existing history is verified before append;
- missing optional credentials do not break the credential-free baseline hash chain;
- audit evidence never grants Human approval, merge, release or production authority;
- private reasoning, prompts, secrets and signing private keys are excluded.
