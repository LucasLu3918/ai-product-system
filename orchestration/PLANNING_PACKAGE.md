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

When independent review is required, persist the review contract and evidence pointer with the planning/validation artifacts: reviewer task mode, read-only boundary, allowlisted packet provenance, exact candidate binding, and the runtime attestation verification status. Store only evidence needed to reproduce the decision; never copy implementation chat, hidden reasoning, scratchpads, or raw traces into the package. Missing trusted verification remains `UNVERIFIED` and is not waived by planning metadata.

Genuinely non-applicable artifacts/dimensions are marked N/A with a reason.

## Quality and delivery planning

既有專案的核心契約變更應在 Change Impact 中列出風險、traversal seed、候選 consumer 與不確定性；依風險設定有界檢查，並在驗收時核對 affected-but-unchanged 節點。Traversal 僅提供候選證據，不取代範圍核准、測試或 diff reconciliation。

若以結構化處置關閉 unknown，計畫與驗收證據應保留原始描述、resolution、可驗證 evidence 與 Human review；只有完成 implementation 後的 exact diff reconciliation 才能將 Change Impact 標為 READY。

需求規劃 validator 契約以 EARS 情境對應驗收證據；該測試檔單獨變更只需 Scenario Conformance 文件閉包，規劃行為、模板及 canonical requirements 仍需完整規劃閉包。

If a plan includes external execution, record the requested minimum isolation and data class in the Execution Profile. Provider verification status is evidence, not permission to transfer a source payload; source scope and destination must be authorized before staging.

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
When scope changes Remote Git publication controls, define the mandatory candidate scan, redaction and history coverage as acceptance criteria; keep external scanner credentials optional unless separately approved.

For runtime integrations that move data outside the project boundary, specify destination, data classes, protected assets, Change Boundary, minimum runtime enforcement, exact approval needs and the network isolation evidence expected at execution time.

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

When publication tooling or documentation placement rules change, use `aips publish preview` before commit to identify the complete canonical document closure and Core Matrix binding; planning approval remains a separate human decision.

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
