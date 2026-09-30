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
├── PLANNING_MANIFEST.yaml    # optional Planning Package v2 machine contract
├── PLANNING_INDEX.md
├── PRODUCT_RESEARCH.md      # when evidence-backed product decisions are needed
├── PRODUCT_PLAN.md
├── REQUIREMENTS.yaml          # optional traceable requirement registry
├── EXPERIENCE_DESIGN.md
├── VISUAL_SYSTEM.md
├── DOMAIN_MODEL.md          # when domain/data behavior is material
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

## Planning Package v2 contract

Use `PLANNING_MANIFEST.yaml` for new v2 packages that need machine-checkable artifact state, applicability, dependency and traceability. Existing packages without a Manifest remain valid legacy packages. Do not require repository-wide migration.

The Manifest declares each artifact as `applicable` or `not_applicable`. Applicable artifacts have a package-relative path and one status: `NOT_STARTED`, `IN_PROGRESS`, `NEEDS_DECISION`, `READY_FOR_REVIEW`, `APPROVED` or `STALE`. Non-applicable artifacts use `status: N/A` and a reason. Dependencies declare `required`, `recommended` or `conditional`; only required dependencies block an artifact from becoming ready. Reject missing/escaping paths, unknown references, duplicate IDs and dependency cycles.

The package lifecycle is `DISCOVERY → PLANNING → REVIEW → GATE_1_READY → GATE_1_APPROVED → IMPLEMENTATION_READY`. Gate 1 and Gate 2 approval evidence is supplied by a human. A validator may verify that evidence is present; it must never create or infer approval. Gate 2 remains separate from Gate 1.

For traceable requirements, the Manifest maps every requirement ID and acceptance ID to applicable downstream artifact IDs. A target may be marked not applicable only with a reason. Assign stable IDs such as `SCR-NNN` for screens, `VIS-NNN` for visual components, `DOM-NNN` for domain concepts and `OP-NNN` for API operations. Planned verification references describe intent, not executed passing evidence.

Run both checks when the package contains `PLANNING_MANIFEST.yaml`:

~~~bash
python scripts/requirements_traceability.py <package>/REQUIREMENTS.yaml --format json
python scripts/planning_package_validate.py <package> --format json
~~~

The Planning Package validator is deterministic and structural. It cannot assess whether research is true, product scope is good, UX is usable, API design is optimal or architecture is appropriate. Use the existing Product Manager, Product Designer, Software Architect, Database Engineer, Backend Engineer, Security Engineer, Quality Reviewer and Delivery Planner for relevant semantic cross-review; do not create a Planning Reviewer Role.

## Discovery and research

Proceed one material decision group at a time. Use a safe professional default when it resolves a non-blocking detail and record it as an assumption. Offer a small set of understandable options with a recommendation when the user must decide. Do not ask users to design schemas, APIs or infrastructure before those choices are required.

Use `PRODUCT_RESEARCH.md` when current external product, user, market or competitor evidence materially informs a product decision. Record sources, observed dates, geography, evidence type, confidence, freshness and limitations. Keep facts/observations distinct from inference, recommendation, assumption and unknown. Visual reference research remains under `creative-reference-research`.

## Domain, UX and API traceability

For REST/OpenAPI implementation readiness, record whether the contract is canonical, descriptive, proposed or unresolved, and identify the exact baseline source when compatibility analysis is required. A structural comparison cannot replace Human approval of breaking changes.

Create stable screen IDs and map primary requirements to journeys, flows, screen responsibilities, interaction states, responsive behavior and accessibility. Create a `DOMAIN_MODEL.md` when domain concepts, lifecycles, ownership or invariants affect the product; model those concepts before choosing persistence technology. Specify API operations from consumer needs and domain behavior, including authorization, validation, errors, retry/idempotency, concurrency and compatibility as applicable.

Load `references/domains/<domain>/` only when the product needs it. Domain packs provide common terminology, workflows, edge cases and risks; they do not prescribe features for every product. Keep visual system definition in the existing `visual-direction` Skill unless repeated evidence justifies a separate reusable Skill.

When implementation readiness is approved, the Implementation Resolution workflow may project the approved requirement, API authority, Human-confirmed technology/architecture decisions and quality expectations into an `IMPLEMENTATION_PROFILE.yaml`. The profile is a traceable handoff to existing implementation roles; it does not replace the Planning Package, approve the plan, or authorize a migration.

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
For v2, set `GATE_1_READY` only after every applicable artifact is ready, deterministic validation passes, semantic review is completed, and material blocking unknowns are resolved. Then wait for Human approval and record its evidence.

## Gate 2 — Implementation Readiness Approval

After Gate 1, derive Initial Implementation Items + recommended order, identify first milestone/dependencies/tests/risky steps, and obtain explicit implementation approval.
Record Gate 2 approval separately; never infer it from Gate 1.

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
