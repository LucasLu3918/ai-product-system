# Verifiable Governance Audit Chain

## Purpose

AIPS already uses Approval Records and SHA-256 scope fingerprints to decide whether a protected action remains inside Human-approved scope. This protocol adds durable, tamper-evident evidence for later audit without creating a new approval gate.

~~~text
Human Approval / Security Review / Validation / Publish / Release / Production
→ canonical Governance Audit Event
→ SHA-256 event hash
→ previous chain hash + event hash
→ SHA-256 chain hash
→ optional HMAC-SHA256 runtime authentication
→ optional Ed25519 signed checkpoint
→ portable JSONL ledger
~~~

The event template is templates/governance/AUDIT_EVENT.yaml. The deterministic implementation is scripts/governance_audit.py.

## Integrity layers

1. Event hash binds canonical observable fields.
2. Hash chain binds ordering and detects edits/reordering and interior deletion; detecting suffix truncation requires a previously anchored expected chain head/event count or equivalent external checkpoint evidence.
3. HMAC-SHA256 optionally authenticates a configured runtime using secret material from an approved secure source.
4. Ed25519 checkpoint optionally signs a chain head so an offline auditor can validate a public key without receiving the signing private key.

HMAC is shared-secret authentication, not asymmetric non-repudiation. Signed checkpoints are the preferred long-term independent-authentication anchor.

## Event boundary

Record governance boundary events, not model thoughts or every tool read. Typical events include HUMAN_APPROVAL_GRANTED, HUMAN_APPROVAL_REVOKED, APPROVAL_STALE, SECURITY_REVIEW_COMPLETED, SECURITY_RISK_ACCEPTED, VALIDATION_COMPLETED, GIT_PUBLISH_AUTHORIZED, GIT_PUBLISHED, PR_MERGED, RELEASE_READINESS_READY, RELEASE_READINESS_BLOCKED, PRODUCTION_DEPLOYED, PRODUCTION_VERIFIED, ROLLBACK_STARTED, ROLLBACK_COMPLETED and AUDIT_KEY_ROTATED.

Events should bind exact approval IDs/fingerprints, candidate commits, operations, results and evidence digests when those values exist.

## Secret and key handling

- Never persist an HMAC secret or signing private key in Git, prompts, ledger events, fixtures or Actions artifacts.
- Ledger events store only key IDs, MAC/signature values and public-key fingerprints.
- Existing authenticated/signed history must be verified before append; missing verification material blocks append.
- The baseline hash chain requires no external Agent/provider credential and no model/API call.

## Verification

Verify always checks sequence, event hashes and chain hashes. Supplied HMAC/public-key material is also validated. require-auth-verification and require-checkpoint-verification make missing verification material for recorded authenticated/signed evidence fail closed. expected-chain-head and expected-events bind the audit to an externally retained anchor and therefore detect tail truncation.

## Assurance guidance

- SAL 0-1: normally optional.
- SAL 2: protected publication/release may use the hash chain.
- SAL 3: approval/security/release evidence should be chained when auditability is material.
- SAL 4: production-relevant governance evidence should use authenticated events and periodic signed checkpoints unless a governed equivalent-assurance decision says otherwise.

## Trust and authority

The chain proves consistency of recorded evidence, not absolute wall-clock truth. A chain file by itself also cannot prove that its final suffix was not removed; retain/distribute a known chain head + event count or equivalent signed checkpoint anchor when truncation resistance is required. High-value events should bind durable anchors such as Git commit SHA, merged PR identity, Actions run/evidence digest or deployment identity.

Audit evidence is downstream of Human authority. A ledger event containing APPROVED never authorizes an action.
