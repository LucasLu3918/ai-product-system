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


## Portable Governance Audit Bundle

When evidence must survive outside the original runner/chat/repository context, use the existing helper rather than inventing a second audit system.

~~~text
verified AUDIT.jsonl
+ exact repository revision
+ selected validation / release / deployment evidence files
+ checkpoint public keys
→ bundle-create
→ MANIFEST.json + AUDIT.jsonl + evidence/* + public-keys/* + ANCHOR.json
→ distribute/store ANCHOR.json independently when truncation/resubmission resistance is required
→ bundle-verify --anchor <retained-anchor>
~~~

Rules:

- bundle creation first verifies the ledger; signed checkpoint history fails closed if its public key is unavailable or invalid;
- HMAC material can be supplied to authenticate history during creation/verification but is never copied into the bundle;
- evidence inputs are explicit `NAME=PATH` files and are copied by digest; source absolute paths are not persisted;
- `repository_revision` must bind the exact Git candidate being audited;
- `MANIFEST.json` binds the ledger SHA-256, event count, chain head, evidence SHA-256, public-key SHA-256/fingerprint and authority=false declarations;
- `ANCHOR.json` binds repository revision + event count + chain head + MANIFEST digest;
- the bundle's internal anchor detects accidental/local mismatch but is not independent trust. Retain/distribute the exported anchor separately, or rely on an independently trusted signed checkpoint, to resist wholesale bundle replacement;
- the format is directory-based and credential-free so it can be copied to offline media without requiring GitHub, a model provider, blockchain or timestamp service.

Example:

~~~bash
python scripts/governance_audit.py bundle-create \
  --ledger AUDIT.jsonl \
  --output audit-bundle \
  --repository-revision <exact-git-sha> \
  --evidence validation=integration-gate-report.yaml \
  --checkpoint-public-key release-key=release-public.pem \
  --anchor-output retained/ANCHOR.json

python scripts/governance_audit.py bundle-verify \
  --bundle audit-bundle \
  --anchor retained/ANCHOR.json
~~~

Bundle evidence never grants approval, merge, release, publication or production authority.


## Governance Audit Catalog and Retention

v0.50 adds a deterministic catalog over existing v0.49 bundles. It does not replace bundle verification.

~~~text
verified portable bundles + retained anchors
→ catalog-build
→ CATALOG.json
   - subject / bundle id
   - exact repository revision
   - event count / chain head
   - manifest + anchor digests
   - evidence digests
   - checkpoint key ids + fingerprints
→ catalog-find
→ auditor locates exact bundle
→ bundle-verify with retained external anchor
~~~

Checkpoint key rotation is represented by distinct key IDs. Reusing the same key ID with a different public-key fingerprint is a fail-closed catalog error. The catalog therefore preserves which releases/deployments depended on which verification keys without acquiring key-rotation authority.

Retention is governed by config/governance-audit-retention.yaml. Its durations are operational defaults, not legal/regulatory requirements.

~~~text
catalog + retention policy + explicit as-of date
→ retention-plan
→ KEEP_FULL | HOLD_FULL | REVIEW_DUE
→ optional minimal digest record for Human review
~~~

REVIEW_DUE never means delete. The helper has no delete or compact command. Every plan emits automatic_delete=false and deletion_authorized=false. Legal hold always wins.

For SAL 2+ the default policy requires an independently supplied anchor at catalog registration. SAL 4 requires at least one verified signed checkpoint. Public-key retention remains part of the audit evidence lifecycle so old signed checkpoints can still be verified after key rotation.
