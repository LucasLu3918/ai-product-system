# Core Change Proposal: Risk-Adaptive Bounded Change Impact Traversal

## System Improvement Review

- **Appropriateness:** Suitable as a candidate extension. Existing Change Impact requires consumer/caller review but does not define directional traversal depth or how to report affected files outside the diff.
- **User problem:** A response-shape or shared-contract change can leave a downstream consumer unchanged and broken while changed-file reconciliation still passes.
- **Proposed solution:** Add deterministic, provider-neutral, bounded caller/consumer traversal, classify affected-but-unchanged nodes, expose truncation and unresolved relationships, and compare against synthetic ground truth before default adoption.
- **Existing coverage:** Project Intelligence has an architecture Impact Graph, SQLite chunks/symbols/history, and exact-identifier two-hop retrieval. The latter is retrieval discovery through bridge chunks, not a caller-to-caller's-caller graph. Change Impact already validates exact post-implementation Git state.
- **Reuse / extension:** Extend `retrieval_intelligence.py`, `project_intelligence.py`, existing Change Impact artifacts, scenario/evidence suites, and architecture docs. Store code relations only in the rebuildable index and run-specific findings in Change Impact evidence.
- **Lower-layer alternative:** A human checklist is simpler but does not provide repeatable candidate discovery; retain it as fallback for dynamic relationships.
- **Context / maintenance cost:** No new always-loaded role or gate. Traversal occurs for changes whose risk policy requires it; hard node/edge/depth bounds and compact per-change evidence cap cost.
- **Security / reliability:** Local-only analysis; source remains in the project workspace and no new service is used. Secret paths remain excluded. Unknown or truncated critical consumers cannot be represented as complete.
- **Backward compatibility:** Preserve current Impact Graph and legacy `impact_graph_reviewed`; add versioned optional traversal evidence. Legacy READY remains subject to existing exact Git checks. Any stricter readiness behavior must be additive and explicitly validated.
- **Scenario / test impact:** Add caller depth, response-shape `.map()` consumer, no-fanout, cycles, truncation, stale index, rename/delete, dynamic unresolved, schema/event subscriber, and risk-class tests. Compare candidate against hand-authored ground truth.
- **Human / agent docs:** Update Change Impact, Project Intelligence, architecture overview and review guidance. Update architecture diagram only where flow representation changes.
- **Architecture diagram impact:** `docs/ARCHITECTURE.md` and `docs/human/ARCHITECTURE_OVERVIEW.md` affected; `project-intelligence-overview.svg` affected if its current flow omits the traversal and evidence layers. Inspect before editing.
- **Constitution impact:** NO. No authority, precedence, safety boundary, or approval rule changes are intended.

## Purpose

Find and review likely callers and consumers beyond changed files without claiming complete static semantics. Establish quality and cost evidence before using the candidate as default Change Impact behavior.

## Why this is a core/large change

The proposal changes existing-project mutation analysis, Change Impact evidence, review behavior, and potentially READY eligibility across projects and languages.

## Proposed Scope

### In scope

- Define edge semantics and risk-adaptive caller/consumer depth, explicit stop reasons, and hard traversal budgets.
- Add a rebuildable relation index or equivalent derived representation using existing dependencies and secret-path exclusions.
- Emit versioned per-change evidence for seeds, edges, provenance, exact/inferred/unresolved relationships, truncation, and affected-but-unchanged dispositions.
- Add bounded synthetic trial and deterministic evaluation against ground truth; preserve candidate output separately until adoption criteria pass.
- If evaluation passes, integrate the evidence contract with existing Change Impact, review guidance, and post-diff validator.
- Add impact-derived tests, scenarios, documentation, and relevant architecture diagram updates.

### Out of scope

- Greptile/SaaS dependency, remote source upload, cross-repository traversal, compiler-grade completeness claim, Neo4j or another database, unbounded recursion, and fixed two-hop enforcement for every change.
- New Role, Skill, approval gate, parser/LSP service, or Constitution change.
- Automatically modifying every affected-but-unchanged file; each candidate requires a disposition.

## Expected Files / Modules

- Core: `scripts/retrieval_intelligence.py`, `scripts/project_intelligence.py`, `orchestration/CHANGE_IMPACT.md`, `orchestration/PROJECT_INTELLIGENCE.md`, `templates/intelligence/CHANGE_IMPACT.yaml`.
- Evaluation: new or extended `tests/evidence/`, `tests/scenarios/`, `tests/validation/`, `tests/scenario_coverage.yaml`, `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`.
- User/agent documentation: `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, `docs/human/PROJECT_INTELLIGENCE.md`, and applicable review docs/diagrams.
- Documentation placement contract: `config/documentation-placement.yaml` registers Scenario 175 in the canonical Conformance section.
- This proposal and its test matrix.

## Impact

### Architecture / Contracts

Three layers: canonical architecture Impact Graph; rebuildable code-relation index; per-change traversal evidence. Caller/callee and consumer/subscriber edges remain distinct. Existing `READY` Git reconciliation remains authoritative for changed files; impact completeness is an additional review dimension.

### Data / Migration

No new persistent database. Extend disposable SQLite index schema through its existing rebuild path. Add optional/versioned traversal YAML fields. Keep older DRAFT and IMPLEMENTATION_APPROVED artifacts readable; legacy READY keeps existing exact Git validation and receives no invented traversal evidence.

### Security / Reliability

Stay local and bounded; preserve index secret-path exclusion and output redaction. Stale/unavailable index yields explicit UNKNOWN/INCOMPLETE. No caller found is not evidence of no impact. High-risk truncation or unresolved critical consumer blocks complete impact status.

### Compatibility / Rollback

Existing index is disposable and force-rebuildable. Roll back code/docs/templates by source revert; no project data migration or runtime service. If a persisted evidence field is introduced, unknown versions must fail clearly without corrupting the existing artifact.

### Tests / Validation

Impact-derived matrix: `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`. Test direct caller and caller's caller, response-shape consumer outside diff, false positives, leaf changes, fan-out cap, cycles, stale index, unresolved dynamic edges, exact diff reconciliation, and backward compatibility. Repository validation and exact-candidate Integration Gate are required.

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Relation extraction and bounded traversal | Yes | Yes | Yes | Yes | N/A | Yes | Index rebuild | Yes | Yes | No UI |
| Change Impact evidence and READY | Yes | Yes | Yes | Yes | N/A | Yes | Legacy artifact compatibility | Yes | Yes | No UI |
| Candidate evaluation and ground truth | Yes | Yes | Yes | Yes | N/A | Synthetic data only | N/A | Evaluation CLI | Yes | No persisted user data |
| Documentation and architecture flow | N/A | N/A | Repository validation | Scenario coverage | N/A | N/A | N/A | N/A | Yes | No executable UI |

Recompute trigger if scope expands: any new relation type, parser/provider, persistent artifact, mutation of affected consumer files, or change to human approval/READY authority.

Required release/CI evidence: candidate-bound Core Matrix, exact local Integration Gate PASS, repository validation, scenario evidence, and all required GitHub checks green.

### Secret / Credential Impact

Secrets required: NO
Approved acquisition mechanism: N/A
Leakage/redaction review: synthetic secret-path and secret-like content cases; ensure findings include bounded source locations without raw sensitive values.
Rotation/revocation plan if exposure is found: N/A; use synthetic fixtures only.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: AFFECTED — show the canonical graph, rebuildable relation index, bounded traversal, and run evidence if the diagram describes Project Intelligence.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — explain impact traversal and its unknown/truncation limits.
- Human SVG architecture/lifecycle diagrams: inspect `docs/human/assets/project-intelligence-overview.svg`; update only if its depicted flow is affected.

## Risks

- Identifier matching can create false caller edges; record resolution quality and evaluate precision.
- Dynamic dispatch, DI, reflection, route/event registries, and configuration wiring remain incomplete.
- More symbols or paths can increase local CPU, index size, and context output; hard budgets and compact summaries are required.
- A new READY hard block could break legacy workflows; adoption and migration behavior must be additive and tested.
- Candidate evaluation must not be represented as adoption evidence unless ground truth, sample coverage, and costs are reported.

## Recommendation

Extend existing local retrieval and Change Impact. Run a bounded candidate and compare to ground truth. Adopt only if the required cases improve without material regression or budget violations. No new service, gate, role, or database.

## Proposed Implementation Order

1. Finalize edge/hop semantics, risk classes, budgets, status contract, and compatibility behavior.
2. Implement a deterministic candidate relation traversal behind an explicit candidate path.
3. Add synthetic fixtures and evaluate candidate vs baseline with predeclared thresholds.
4. Use the user's instruction to proceed with adoption only if the candidate meets those thresholds; otherwise stop and report evidence.
5. Integrate the passing contract with Change Impact, review, READY, docs, scenarios, and tests; validate exact candidate.

## Approval

Status: APPROVED
Approved by: User
Approved at: 2026-09-24 15:44 UTC
Approval record: User explicitly requested implementation of all recommendations from `plan2.md`, local validation, and a remote PR merged to `main`; implementation is constrained to this proposal. Candidate adoption is conditional on meeting the stated evidence thresholds.
Proposal fingerprint: pending exact candidate
Scope fingerprint: pending final changed-file set
