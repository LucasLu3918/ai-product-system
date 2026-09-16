# End-to-End Product Delivery

Use when the user wants a complete product rather than an isolated change.

## Goal

Deliver a product that is understandable, reproducible, locally operable, testable and reviewable. Production enablement is a second milestone unless the user explicitly requested production from the start.

## Lifecycle

~~~text
User Request / Assets
→ Guided Discovery
→ Product Workspace + PRODUCT.yaml
→ Quality Planning + QUALITY_PROFILE.yaml
→ Reproducible Planning Package
→ Gate 1: Planning Approval
→ Architecture / UX / Brand / API / Data / Security / Delivery Design
→ Gate 2: Implementation Readiness Approval
→ Deployment Units + Local Environment
→ Implementation
→ Local Verification
→ Security / Quality / Performance / Usability Review as applicable
→ LOCAL_COMPLETE
→ Production requested already?
   ├─ yes → Production Enablement
   └─ no  → ask whether to continue to Production
               ├─ no  → persist Local completion + future deployment notes
               └─ yes → Production Enablement
→ Infrastructure / CI/CD / Secrets / Domain / Data / Recovery
→ Observability Infrastructure
→ Staging when applicable
→ Release Readiness
→ Production Promotion
→ Health / Smoke / Logs / Metrics / Alerts
→ Rollback / Roll-forward when required
→ PRODUCTION_VERIFIED
~~~

## Delivery milestones

### LOCAL_COMPLETE

A product may be complete for local use before any hosting/cloud decision is made.

LOCAL_COMPLETE requires applicable:

- functional acceptance criteria satisfied;
- reproducible local start path;
- frontend/backend/data integration works locally;
- migrations/local data setup works;
- static/unit/integration/contract/E2E checks;
- required Security Assurance review;
- applicable performance target evidence;
- usability/visual review;
- maintainability/architecture review;
- local reliability/error handling;
- documentation;
- required logging/metrics/tracing instrumentation hooks implemented.

Production infrastructure, hosted monitoring and production secrets are not required for LOCAL_COMPLETE unless the user explicitly included them in scope.

### PRODUCTION_VERIFIED

Requires LOCAL_COMPLETE plus applicable:

- production infrastructure/configuration;
- CI/CD or repeatable deployment automation;
- runtime secrets;
- domain/TLS/networking;
- production database/migration/backup/recovery;
- observability backend/collectors/dashboards/alerts;
- staging verification when applicable;
- Release Readiness;
- production deployment;
- health/smoke/critical-path verification;
- immediate log/metric/alert inspection;
- rollback/recovery path;
- persisted evidence/state.

## Quality planning

For complete products load `orchestration/QUALITY_PLANNING.md`.

Use Q1/Q2/Q3 only as baselines; individual quality dimensions may be independently raised/lowered.

Persist `docs/quality/QUALITY_PROFILE.yaml` when applicable and use its targets/budgets as planning and verification inputs.

## Product Workspace

Prefer one product workspace as the System of Record:

~~~text
product/
├── PRODUCT.yaml
├── README.md
├── .ai/
├── docs/
│   ├── product/
│   ├── quality/
│   ├── design/
│   ├── architecture/
│   ├── api/
│   ├── security/
│   ├── operations/
│   └── decisions/
├── brand/
├── apps/
├── packages/
├── database/
├── tests/
├── infra/
├── deployment/
├── scripts/
└── Makefile
~~~

Create only applicable paths.

## Deployment Units, not forced repositories

Frontend/backend/worker/etc. are independent Deployment Units when they need separate build/test/deploy behavior.

Independent deployability does not require an independent Git repository.

Default to one repository unless team ownership, permission/security boundary, release cadence, scale or shared-service topology materially justifies multi-repo.

## Local developer experience

Every implemented product needs a reliable local start/test path.

Prefer obvious entry commands when practical:

~~~text
make dev
make test
make security
make build
~~~

Do not force Docker when it adds no value.

## Verification layers

Use only applicable layers:

~~~text
Static / Lint / Type
→ Unit
→ Integration
→ Contract
→ E2E
→ Security
→ Performance / UX / Reliability evidence as required by Quality Profile
→ Build
→ Smoke
~~~

## Application observability before deployment

Observability requirements are planned before production vendor selection.

During architecture/coding, implement applicable provider-neutral instrumentation:

- structured logs;
- health/readiness endpoints;
- metrics hooks;
- trace context/instrumentation;
- correlation/request IDs;
- separate audit logging for high-value/security-sensitive actions.

Never log credentials, tokens, secrets or prohibited sensitive payloads. Define redaction rules.

Production baseline is structured logs + health check. Other capabilities are risk-proportional.

## Production Enablement

Choose concrete hosting/observability technology only after the target environment, scale, budget and operational preferences are known.

Possible implementations include:

- logs: ELK/Elastic, Loki, cloud/managed logging;
- metrics: Prometheus or managed metrics;
- dashboards: Grafana or provider dashboards;
- traces: OpenTelemetry with Tempo/Jaeger/APM;
- alerts: Alertmanager, Grafana/provider alerting.

These are implementations, not hard-coded system requirements.

## Environments

Typical production flow:

~~~text
local → CI → staging → production
~~~

Staging is default for material networked production systems and may be N/A with a reason for sufficiently simple/low-risk products.

## Deployment automation

Create the smallest repeatable automation supported by the target platform.

If access/credentials/connectors are unavailable, persist runnable configuration and mark Production Enablement BLOCKED rather than claiming success.

## Secrets

Never persist real secrets in the repository. Use examples/references only and target-platform secret/configuration facilities at runtime.

## Data migration and recovery

When persistent data/schema changes exist, include migration order, compatibility, backup/recovery, verification and rollback/roll-forward.

## Production completion

Do not describe a local product as production-ready merely because code exists.

Use exact delivery state:

- `LOCAL_COMPLETE`
- `PRODUCTION_VERIFIED`

If the user did not request production initially, ask whether to continue only after LOCAL_COMPLETE has been reached.
