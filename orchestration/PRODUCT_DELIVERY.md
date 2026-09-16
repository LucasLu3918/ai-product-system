# End-to-End Product Delivery

Use when the user wants a complete product delivered from idea/materials through a verified production deployment.

## Goal

Deliver a product that is understandable, reproducible, testable, security-reviewed, deployable, observable and recoverable — not merely source code.

## Lifecycle

~~~text
User Request / Assets
→ Product Intake + Guided Discovery
→ Product Workspace + PRODUCT.yaml
→ Reproducible Planning Package
→ Gate 1: Planning Approval
→ Architecture / UX / Brand / API / Data / Security / Delivery Design
→ Gate 2: Implementation Readiness Approval
→ Deployment Units + Local Environment
→ Implementation
→ Local Verification
→ Security Verification + Independent Review
→ Release Candidate
→ Staging Deployment (default for material production systems)
→ Staging Smoke / E2E / Security Verification
→ Release Readiness
→ Production Promotion
→ Health / Smoke / Logs / Metrics
→ Rollback if required
→ Persist final state/evidence
~~~

## Product Workspace

Prefer one product workspace as the System of Record:

~~~text
product/
├── PRODUCT.yaml
├── README.md
├── .ai/
├── docs/
│   ├── product/
│   ├── design/
│   ├── architecture/
│   ├── api/
│   ├── security/
│   ├── operations/
│   └── decisions/
├── brand/
├── apps/
│   ├── frontend/
│   └── backend/
├── packages/
├── database/
│   └── migrations/
├── tests/
│   ├── integration/
│   ├── contract/
│   └── e2e/
├── infra/
├── deployment/
├── scripts/
└── Makefile
~~~

Create only applicable paths. Do not generate empty structure for features that do not exist.

## Deployment Units, not forced repositories

Frontend/backend/worker/etc. are independent Deployment Units when they need separate build/test/deploy behavior.

Independent deployability does not require an independent Git repository.

Default:
- use one repository when it keeps contracts, docs and cross-component testing simpler;
- split repositories only when team ownership, permission/security boundary, release cadence, scale or shared-service topology materially justifies it.

PRODUCT.yaml records each unit and its repository/path.

## Local developer experience

Every implemented product must document a reliable local start/test path.

Prefer one obvious entry command when practical, for example:

~~~text
make dev
make test
make security
make build
~~~

The underlying mechanism may be Docker Compose, native runtimes or project-specific tooling. Do not force Docker when it adds no value.

## Verification layers

Use only applicable layers:

~~~text
Static / Lint / Type
→ Unit
→ Integration
→ Contract
→ E2E
→ Security
→ Build
→ Smoke
~~~

Security is both design-time and verification-time:
- Risk Profile / Threat / Authorization / Business invariants during planning;
- deterministic scanners/tools where applicable;
- independent Security Engineer reasoning for material boundaries;
- SAL requirements remain authoritative.

## Environments

Typical formal flow:

~~~text
local → CI → staging → production
~~~

Staging is default for material networked/production systems. It may be N/A for low-risk static or otherwise simple products when the reason is recorded.

## Deployment automation

For complete-product delivery, create the smallest repeatable deployment automation supported by the target platform, such as CI/CD configuration, infrastructure/deployment code or a bounded deployment script.

Requirements:
- build/test/deploy steps are reproducible;
- staging uses the same release candidate path/artifact strategy as production where practical;
- secrets come from approved runtime secret/configuration facilities, not source control;
- deployment commands/pipelines are persisted in the Product Workspace;
- automation is verified in staging before production when staging is applicable;
- if required platform access/credentials/connectors are unavailable, persist the runnable configuration and mark deployment BLOCKED rather than claiming success.

When tools/platform access are available and the approved release flow permits it, execute the deployment automation and continue with verification instead of stopping at documentation.

## Production promotion

Deployment automation is the default goal for a complete product; unconditional automatic production promotion is not.

Release Readiness determines whether promotion is technically ready. Human approval requirements remain risk-proportional and follow existing governance.

High-risk or difficult-to-recover production promotion requires explicit approval.

## Secrets

Never persist real secrets in the product workspace/repository.

Store examples/references only (for example `.env.example`). Runtime secrets belong in the target platform's approved secret manager/configuration facility.

## Data migration

When persistent data/schema changes exist, include:
- migration order;
- compatibility strategy;
- backup/recovery as applicable;
- verification;
- rollback/roll-forward plan.

## Production completion

Production deployment alone is not Done.

Completion requires applicable:
- deployment success;
- health check;
- smoke/E2E verification;
- logs/metrics/alerts available;
- security/release evidence persisted;
- rollback/recovery path known;
- PRODUCT.yaml and workspace state updated.
