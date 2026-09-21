# Scenario 159 — Portable Governance Audit Bundle

A maintainer must be able to hand an offline auditor a self-contained, deterministic evidence bundle without exposing HMAC/signing secrets or trusting an Agent narrative.

Expected:
- bundle creation refuses invalid ledger history and requires public-key verification for recorded signed checkpoints;
- MANIFEST binds exact repository revision, ledger SHA-256, event count, chain head, evidence digests and bundled public-key fingerprints;
- ANCHOR binds repository revision + event count + chain head + MANIFEST digest and can be exported for independent retention;
- bundle verification with a retained external anchor detects ledger truncation, evidence tamper, public-key tamper, missing files and anchor tamper;
- HMAC secrets and signing private keys are never persisted in the bundle;
- source absolute paths are not persisted;
- baseline bundle creation/verification requires no external Agent/provider credential or network service;
- bundle evidence grants no Human approval, merge, release, publication or production authority.
