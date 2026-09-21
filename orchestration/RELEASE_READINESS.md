# Release Readiness

Use before promoting an exact release candidate to production.

## Purpose

Release Readiness is the consolidated production-readiness decision. It is not required merely to declare LOCAL_COMPLETE.

It answers:

> Is this exact candidate sufficiently built, tested, security-reviewed, recoverable and observable for this production environment?

## Inputs

Use applicable evidence from:

- PRODUCT.yaml;
- approved QUALITY_PROFILE.yaml;
- exact release candidate/version/commit;
- test/build/security evidence;
- migration/recovery evidence;
- staging evidence;
- observability/operations configuration.

## Required evidence

Assess only applicable items:

- all Deployment Units build;
- static/unit/integration/contract/E2E checks;
- Quality Profile production targets that must be verified before promotion;
- required Security Assurance evidence, including secret/credential leakage/handling evidence when applicable;
- migrations/recovery validated;
- infrastructure/configuration validated;
- staging verified when applicable;
- structured logs + health check available;
- required metrics/traces/dashboards/alerts available;
- required audit logging available;\n- when governance auditability is required by the affected SAL/change boundary, bind the exact candidate into the verifiable Governance Audit Chain;
- when long-lived/offline audit transfer is required, export a portable Governance Audit Bundle containing the exact candidate revision, retained chain anchor, applicable evidence digests and checkpoint public keys;\n- when audit evidence must remain discoverable across releases/deployments, register the verified bundle in the Governance Audit Catalog and evaluate the advisory retention policy;
- deployment/runbook/rollback documentation;
- unresolved blockers.

Use `templates/delivery/RELEASE_READINESS.yaml`.

## Status

- READY — all applicable production technical/readiness conditions satisfied.
- NOT_READY — evidence/work remains.
- BLOCKED — a release blocker exists.

READY never bypasses human/security/governance approval.

## Candidate integrity

Readiness applies to one exact release candidate/version/commit set. Material code/config/infra changes invalidate affected evidence.

## Post-deploy

After production promotion:

1. verify deployment status;
2. run health/smoke checks;
3. confirm critical user path where practical;
4. inspect logs/metrics/alerts for immediate regressions;
5. verify required SLO/business indicators when available;
6. rollback/roll-forward on failed verification;
7. persist PRODUCTION_VERIFIED state only after applicable checks pass.


## Audit retention readiness

A release gate may require proof that its audit bundle is registered and discoverable, but catalog/retention evidence cannot make an otherwise NOT_READY or BLOCKED release READY. A retention REVIEW_DUE state also does not authorize evidence deletion; any destructive action requires separate Human authority.
