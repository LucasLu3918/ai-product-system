# Reproducible Planning Package

Use when the task creates or materially revises the primary definition of a product/project.

## Workspace first

Resolve the persistence workspace before producing the authoritative plan.

For complete product delivery, initialize PRODUCT.yaml and use `orchestration/QUALITY_PLANNING.md`.

## Required planning artifacts

Create the smallest complete set another competent Agent/team can execute without hidden chat context.

Recommended package:

~~~text
planning/
├── PLANNING_INDEX.md
├── PRODUCT_PLAN.md
├── REQUIREMENTS.yaml          # optional traceable requirement registry
├── EXPERIENCE_DESIGN.md
├── VISUAL_SYSTEM.md
├── TECHNICAL_ARCHITECTURE.md
├── API_SPEC.md
├── IMPLEMENTATION_PLAN.md
├── DECISIONS_ASSUMPTIONS.md
├── brand/                    # when applicable
└── security/                 # required for applicable SAL
~~~

For complete products also persist/link the Quality Profile, normally:

`docs/quality/QUALITY_PROFILE.yaml`

Genuinely non-applicable artifacts/dimensions are marked N/A with a reason.

## Quality and delivery planning

Before architecture is locked:

1. classify Q1/Q2/Q3 baseline;
2. derive seven quality dimensions;
3. establish initial resource/cost/time ranges with confidence;
4. define measurable targets/budgets and verification methods;
5. plan provider-neutral logging/health/metrics/tracing/audit requirements;
6. record material trade-offs.

After architecture/dependency choices, refine resource/cost/time estimates.

## PLANNING_INDEX.md

Include package purpose/version/status, authoritative links, approval state, applicable/N/A matrix, reproducibility checklist and blocking decisions.

## PRODUCT_PLAN.md

Include vision/problem, target users, goals/non-goals, scope/release boundary, functional/non-functional requirements, acceptance criteria, business rules, constraints and success metrics. Use EARS patterns for atomic functional behavior when they improve clarity; do not force narrative, assumptions or non-functional targets into EARS. Keep targets and verification methods explicit.

When requirement-to-acceptance traceability benefits from a structured record, include the optional `templates/planning-package/REQUIREMENTS.yaml` as `REQUIREMENTS.yaml` in the package. Assign stable requirement and acceptance IDs, link each requirement to its acceptance criteria, and record a verification method. Retain rationale, sources and unresolved decisions in the Product Plan / DECISIONS_ASSUMPTIONS.md. Run `python scripts/requirements_traceability.py <package>/REQUIREMENTS.yaml` to check structure and ID uniqueness; add `--format json` for machine-readable PASS/FAIL status. The CLI exits zero on structural success and non-zero on validation failure. Evidence references identify planned or existing evidence; only executed evidence may be reported as test results, and AIPS Scenario Conformance continues to cover AIPS Scenarios only.

## EXPERIENCE_DESIGN.md

Include information architecture, key journeys, screen/page inventory, interaction states, responsive/accessibility behavior, UX rationale and edge cases.

## VISUAL_SYSTEM.md

Include visual direction, key visual, typography/color/spacing/iconography/imagery, design-token/component guidance, consistency rules and assets.

## TECHNICAL_ARCHITECTURE.md

Include:

- system context/components;
- Clean Architecture/DDD profile where justified;
- data/storage/integrations;
- trust/security boundaries;
- performance/scalability assumptions;
- Quality Profile implications;
- provider-neutral structured logging/health/metrics/tracing/audit instrumentation requirements;
- Deployment Units/repository strategy;
- local environment;
- production-enablement assumptions if known;
- failure/recovery considerations;
- diagrams where useful.

Do not select an ELK/Prometheus/Grafana/etc. stack merely because observability is required; choose concrete services after production environment/operations constraints are known.

## API_SPEC.md

When applicable define operations, auth/authz, request/response, validation/errors, pagination/filtering/idempotency/versioning/examples/compatibility. Prefer machine-readable contracts where appropriate.

## Security assurance

Classify Product Baseline SAL and Reliability Impact during planning.

SAL 3–4 persist applicable security artifacts under planning/security. SAL4 economic-value features explicitly cover authorization, transaction/idempotency/replay/concurrency, audit/reconciliation and recovery.

## IMPLEMENTATION_PLAN.md

Describe implementation readiness:

- workstreams/dependencies/risks;
- testing strategy;
- milestones;
- local commands;
- Quality Profile verification;
- initial and refined resource/time/cost estimate;
- LOCAL_COMPLETE Definition of Done;
- Production Enablement plan when already requested;
- CI/release/staging/production flow where applicable;
- migration/recovery;
- observability/runbook expectations.

## DECISIONS_ASSUMPTIONS.md

Track FACT / ASSUMPTION / PROPOSAL / ACCEPTED DECISION / UNKNOWN / deferred decisions.

## Gate 1 — Planning Package Approval

Persist and cross-review the package, surface material issues, then obtain user planning approval. Do not start implementation yet.

## Gate 2 — Implementation Readiness Approval

After Gate 1, derive Initial Implementation Items + recommended order, identify first milestone/dependencies/tests/risky steps, and obtain explicit implementation approval.

## Reproducibility standard

Another competent Agent/team must be able to answer without hidden chat context:

- what/why/who/scope;
- expected UX/visual behavior;
- APIs/data/business rules;
- quality/security/performance/reliability targets;
- resource/cost/time expectations and confidence;
- architecture decisions/assumptions;
- how to run/test/review locally;
- what LOCAL_COMPLETE means;
- whether Production Enablement is in scope;
- how production would be deployed/observed/recovered when applicable;
- which artifacts are authoritative.
