# Scenario 160 — Governance Audit Retention & Verification Policy

A maintainer must be able to discover the correct Governance Audit Bundle across multiple releases/deployments, preserve checkpoint key-rotation evidence, and evaluate retention without granting automatic deletion authority.

Expected:
- catalog-build verifies each registered bundle and binds its independently supplied anchor when required by SAL;
- the catalog indexes bundle identity, subject, repository revision, event count, chain head, manifest/anchor digests, evidence digests and checkpoint public-key fingerprints without persisting source absolute paths;
- catalog-find can deterministically locate evidence by repository revision, subject, bundle id, chain head or checkpoint key id;
- reusing one checkpoint key id with a different public-key fingerprint fails closed, while rotation to a distinct key id remains auditable;
- the retention policy is advisory-only, declares that operational defaults are not legal/regulatory requirements, and never authorizes deletion;
- expired full bundles produce REVIEW_DUE plus a deterministic minimal digest record; no evidence is deleted or compacted automatically;
- legal hold overrides time-based review;
- SAL 4 catalog registration requires signed checkpoint evidence and long-lived checkpoint-key retention guidance;
- catalog tampering causes verification failure;
- no new Agent/provider credential, Role, Skill, Approval Gate, merge authority, release authority or production authority is introduced.
