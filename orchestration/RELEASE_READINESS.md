# Release Readiness

Use before promoting a complete product/release candidate to production.

## Purpose

One consolidated readiness decision replaces many small release gates.

Release Readiness answers:

> Is this exact release candidate sufficiently built, tested, security-reviewed, recoverable and observable for its target environment?

## Required evidence

Assess only applicable items:

- all Deployment Units build successfully;
- static/unit/integration/contract/E2E checks;
- required Security Assurance evidence;
- migrations validated with recovery strategy;
- infrastructure/configuration validated;
- staging deployment and verification when applicable;
- health/log/metric/alert readiness;
- deployment/runbook/rollback documentation;
- unresolved blockers.

Use `templates/delivery/RELEASE_READINESS.yaml`.

## Status

- READY — all applicable technical/readiness requirements satisfied.
- NOT_READY — incomplete evidence/work remains.
- BLOCKED — a release blocker exists, including unresolved security findings that current SAL rules prohibit.

READY does not override governance. Production promotion may still require human approval based on risk, irreversibility and existing release policy.

## Candidate integrity

Readiness applies to one exact release candidate/version/commit set. Material code/config/infra changes after readiness invalidate affected evidence and require re-verification.

## Post-deploy

After production promotion:
1. verify deployment status;
2. run health/smoke checks;
3. inspect logs/metrics for immediate regressions;
4. confirm critical user path where practical;
5. rollback/roll-forward on failed verification;
6. persist production result and evidence.
