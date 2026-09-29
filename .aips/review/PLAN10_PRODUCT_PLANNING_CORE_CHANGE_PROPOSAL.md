# Core Change Proposal: Planning Package Product Planning Capability

## System Improvement Review

- **Appropriateness:** Suitable. ChatGPT conversation `plan10` identifies a repeated gap between product discovery and implementation-ready engineering artifacts. Existing Product Manager, Product Designer, Architect, Database Engineer, Backend Engineer, Security Engineer, Quality Reviewer and Delivery Planner cover the needed judgment; the change extends their shared Planning Package contract.
- **User problem:** Planning content is spread across prose templates, optional requirement traceability and role guidance. A downstream agent can miss assumptions, artifact dependencies, domain boundaries or requirement-to-design/API links.
- **Proposed solution:** Add an optional versioned Planning Manifest and deterministic structural validator; strengthen product research, UX, visual, domain and API cross-artifact templates; add only Product Research and Data Modeling skills; supply an on-demand e-commerce reference pack; retain the existing two Human approval gates.
- **Existing coverage:** Planning Package, product discovery, requirements definition, visual direction, REST API, database-engineer and product-manager capabilities already exist. Scenario Conformance and repository validation are the established evidence paths.
- **Reuse / extension:** Extend existing roles, skills, templates, Product Delivery and validation contracts. Do not create a Planning Reviewer role, Design System skill, e-commerce role, mandatory CLI workflow or always-loaded domain corpus.
- **Compatibility:** Manifest is opt-in. Existing packages without it remain valid; no repository-wide migration is required. EARS stays in use for applicable functional requirements. Machine checks are structural and do not replace semantic review.
- **Constitution impact:** NO. No authority or approval rule changes; Human approval remains authoritative at Gate 1 and Gate 2.

## Purpose

Make a product plan reproducible and directly actionable by another AI or engineering team without relying on hidden chat context, while preserving sources, assumptions, unresolved decisions and cross-artifact traceability.

## Why this is a core change

The change expands the system-wide product planning contract, capability routing, canonical templates, deterministic validation and Scenario Conformance. It also changes the versioned Planning Package shape consumed across product workspaces, while preserving legacy package behavior.

## Proposed Scope

### In scope

- Optional `PLANNING_MANIFEST.yaml` with artifact path, applicability, lifecycle status, dependency strength and per-requirement downstream links.
- Structural validation for paths, dependency cycles, applicability reasons, stable artifact IDs, requirement/acceptance traceability, diagnostics and separate Human approval evidence.
- Evidence-grounded Product Research and clearer Product Plan, experience, visual system, domain model, API and architecture relationships.
- Reuse of existing roles and skills; add `product-research` and `data-modeling` skills only.
- Lazy-loaded e-commerce reference modules for catalog/inventory, cart/checkout, order/payment/refund and operations.
- Ten scenarios (183–192), deterministic/lifecycle contracts, documentation and affected architecture diagrams.

### Out of scope

- Financial modeling, product-market conclusions unsupported by current evidence, automatic market decisions, an e-commerce role, a Planning Reviewer role, a design-system skill, mandatory manifest migration, new approval gate, Constitution change, autonomous implementation approval or claim that structural validation proves semantic quality.

## Expected Files / Modules

- `orchestration/PLANNING_PACKAGE.md`, existing product/design/engineering skills and Product Manager / Database Engineer roles.
- `templates/planning-package/`, new `scripts/planning_package_validate.py`, validation contracts and lifecycle evidence.
- `references/domains/` on-demand e-commerce pack, Scenario 183–192 registry and docs closure.
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` and this proposal.

## Impact

### Architecture / Contracts

Add a versioned optional artifact graph and traceability layer within the existing Planning Package. Reuse existing Human approval gates. Keep research truth, UX quality, domain suitability, security applicability and implementation authorization under human/expert review.

### Data / Migration

Planning data remains package-local YAML/Markdown. No runtime database or persistent service changes. No migration is needed; legacy packages without a Manifest continue to work. Template example evidence paths are explicitly plans, not executed results.

### Security / Reliability

The validator rejects package path traversal, detects symlink escapes, validates unknown IDs and never generates approval evidence. Domain references prohibit invented payment, refund, privacy or regulatory policy and load only when relevant. No credentials or external source corpus are required for baseline validation.

### Compatibility / Rollback

Manifest v1 is opt-in and additive. Revert the templates, validator, skills and docs to roll back; there is no state migration or runtime dependency. Existing EARS traceability stays supported.

### Tests / Validation

- `python scripts/planning_package_validate.py templates/planning-package --format json` — PASS (11 artifacts, 2 requirements).
- `python tests/evidence/planning_package_lifecycle.py` — PASS (canonical package passes; unknown operation and escaping path fail closed).
- `python tests/validate_repository.py` — PASS (v0.67.0, 12 roles, 27 skills, 192 scenarios).
- `python scripts/documentation_placement.py` — PASS.
- `python scripts/scenario_conformance.py check --format json` — PASS (192 registered, 0 uncovered, 191 automated, 1 manual).
- `git diff --check` — PASS.
- Exact-candidate Integration Gate and remote required checks remain to be run after candidate commit/PR.

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Manifest and structural validator | applicable | applicable | lifecycle | applicable | N/A | path containment and gate evidence checks | legacy package preserved | validator CLI | schema/templates | no deployed runtime UI |
| Requirement to artifact traceability | applicable | applicable | lifecycle | applicable | manual product journey | applicable | N/A | validator CLI | requirements/design/domain/API docs | no persisted migration |
| Product research and capability routing | applicable | role/skill contract | N/A | capability registry | manual semantic assessment | no secret inputs | N/A | routing metadata | role/skill docs | judgment requires real product context |
| E-commerce reference pack | YAML/index contract | N/A | N/A | bounded modules | manual applicability | sensitive/payment guidance | N/A | lazy-load index | reference docs | no implementation integration |
| Documentation and Scenario coverage | placement audit | N/A | full repository validation | conformance registry | N/A | security applicability language | N/A | N/A | Human/Agent docs and diagrams | no separate hosted UI |

Recompute trigger if scope expands: new runtime persistence, mandatory legacy migration, changed Gate authority, new domain/role/always-loaded skill, additional public API/runtime command, or a Constitution change.

Required release evidence: complete local validation, exact-candidate Core Matrix and Integration Gate, PR label `aips:core-change`, and all required GitHub checks passing before merge.

### Secret / Credential Impact

Secrets required: NO

Approved acquisition mechanism: N/A

Leakage/redaction review: planning templates and reference guidance forbid raw payment credentials; the candidate secret scan and publication gate remain enabled.

Rotation/revocation plan if exposure is found: N/A; no credential source is introduced.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: AFFECTED — show research/requirements/design/domain/API flow into the optional manifest traceability and existing Gate 1.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — explain optional structure, compatibility, semantic review and Human gates.
- `docs/human/assets/product-delivery-overview.svg`: AFFECTED — update Planning Package artifact coverage and traceability/gate note.
- Other system/harness diagrams: N/A — no runtime, integration or security architecture flow changes.

## Risks

- A rigid template can encourage irrelevant artifacts; per-artifact applicability and explicit reasons keep packages scoped.
- Stable IDs can drift; deterministic trace validation reports broken references but does not make semantic claims.
- Research may become stale; sources and observation dates are retained and research skill requires current evidence.
- Users may treat validator PASS as approval; output and docs explicitly separate structure, semantic review and Human gates.

## Recommendation

Implement as one cohesive minor release (0.67.0), preserve legacy package behavior, and use the existing specialists and Human approvals for all semantic decisions.

## Proposed Implementation Order

1. Define Manifest and structural contract.
2. Add research/domain/UX/visual/API artifact links and reusable skills.
3. Add selective domain references and scenarios.
4. Complete Human/Agent documentation, diagrams, release notes and exact candidate evidence.

## Approval

Status: APPROVED for the implementation scope above, based on the user's current-turn instruction to implement all recommendations from ChatGPT conversation `plan10`.
Approved by: User instruction in this task
Approved at: 2026-09-29 (Asia/Taipei)
Approval record: Current user request in this Codex task: implement all recommendations from `plan10`, validate locally, and prepare PR merge to `main`.
