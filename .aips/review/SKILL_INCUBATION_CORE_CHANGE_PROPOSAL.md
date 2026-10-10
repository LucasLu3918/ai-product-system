# Core Change Proposal — Skill Incubation

## Purpose

Address reusable engineering, operations, testing and game-development guidance gaps identified in the approved skill plan.

## Why this is a core/large change

The change adds 13 canonical Skills and expands three existing Skills, changing reusable task-routing behavior across multiple Capabilities. It also changes the generated registry, scenario coverage, documentation placements and Human guidance, so the candidate needs an exact-boundary Core matrix and full Integration Gate evidence.

## Proposed Scope

### In scope

- Add systematic-debugging, frontend-implementation, llm-feature-integration, e2e-browser-testing, observability-design, database-migration, dependency-upgrade, architecture-decision-record, game-design-document, game-loop-architecture, game-feel, game-balance-economy and level-design.
- Extend ux-web-design with existing-page accessibility audits, performance-profiling with target-device game frame budgets, and product-research with consented playtesting methods.
- Generate skills/INDEX.yaml from canonical metadata; add 16 manual routing/behavior scenarios and a native web DOM/SVG puzzle-game reference.
- Update canonical documentation placements, Architecture and Human current-behavior guidance.

### Out of scope

- New Role or Capability, including a game Capability.
- multiplayer-netcode: the plan makes this conditional on a real-time multiplayer need; no such requirement is present in the selected pilot or this task.
- Changes to agent runtime, model policy, approval gates, CLI behavior, product gameplay code, or user data.
- Claiming real-project pilot, playable vertical slice, or participant playtest completion from this repository-only candidate.

## Expected Files / Modules

Canonical Skill sources under skills/; generated skills/INDEX.yaml; tests/scenarios/241–256-skill-incubation-routing.md and tests/scenario_coverage.yaml; OpenCode Skill projection lifecycle expectations; conformance baseline expectations; references/game-engines/native-web-dom-svg-puzzle-games.md; config/documentation-placement.yaml; docs/ARCHITECTURE.md; Human documentation and generated Conformance views. Active review evidence is in .aips/review/.

## Impact

### Architecture / Contracts

Additive Skill metadata continues the canonical SKILL.md → skill_index.py → compatible v1 INDEX contract. Existing Capability IDs, Roles, host adapters and routing APIs remain unchanged. Current architecture diagrams show the same flow and need no topology changes.

### Data / Migration

No product data, persistence schema, database, or migration changes.

### Security / Reliability

LLM content is explicitly untrusted; tool permissions and application-side authorization remain required. Observability guidance prohibits secrets and high-cardinality personal data in logs/metrics. Dependency, migration, random-reward and playtesting guidance includes provenance, recovery, legal-review and consent boundaries.

### Compatibility / Rollback

Additive files and metadata only. Reverting the candidate restores the previous generated index; no runtime or data migration is required. Existing v1 consumers must pass the Skill Index lifecycle.

### Tests / Validation

Impact-derived Test Matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Skill metadata and compatible INDEX | Required | Skill-index lifecycle | Registry generation/check | v1 shape/unique ID/path | N/A | Required secret scan and content-safety checks | N/A | Skill projection lifecycle | Required | No runtime product behavior changed |
| Manual scenario registry and references | Required | N/A | Scenario Conformance | Coverage/evidence paths | N/A | Content review | N/A | N/A | Required | Specifications are not automated model-routing evidence |
| Human and Agent documentation closure | Required | N/A | Documentation placement/sync | Required placement headings | N/A | Secret scan | N/A | N/A | Required | No user data or runtime contract changed |

Recompute trigger if scope expands: any Role/Capability, adapter, router, runtime code, CLI, database, or product game implementation change.

Required release/CI evidence: repository validation, exact-candidate secret scan, Core Change Test Matrix, local exact-candidate Integration Gate, and required PR checks for the same head SHA.

### Secret / Credential Impact

Secrets required: NO

Approved acquisition mechanism: Not applicable.

Leakage/redaction review: Scan exact candidate and verify content-safety validation; no credentials or private pilot data are added.

Rotation/revocation plan if exposure is found: Follow the repository secret incident process; no new secrets are introduced.

### Documentation / Diagrams

Architecture Diagram Impact:
- docs/ARCHITECTURE.md Mermaid: N/A — canonical Skill routing flow already depicts the unchanged metadata → generator → v1 INDEX → implementation topology; only the capability list changes.
- docs/human/ARCHITECTURE_OVERVIEW.md: AFFECTED — update the Deterministic Execution explanation of on-demand Skills and manual versus deterministic evidence.
- Human SVG architecture/lifecycle diagrams: N/A — no Role, Capability, runtime component, data flow or authority boundary is added.

## Risks

- Poor triggers could route unrelated tasks; non-triggers and per-skill scenarios limit this risk.
- Manual routing scenarios do not prove actual model selection; report them as expected semantic behavior only.
- Real playable game and participant playtest milestones require the external rune-room project and consenting participants; they remain unverified by this AIPS candidate.
- Game balance and accessibility guidance must not present legal advice or overclaim conformance.

## Recommendation

Proceed with the additive Skills and targeted extensions. Keep framework-specific material in references and defer multiplayer netcode until a real product requirement exists.

## Proposed Implementation Order

1. Finalize admitted Skill sources and narrow existing-Skill extensions.
2. Regenerate and verify the Skill Index.
3. Add manual scenarios and reference material.
4. Reconcile documentation placements and generated Conformance summary.
5. Bind the exact candidate to this Core matrix, run the complete local Gate, create the PR and merge only after exact-head required checks pass.

## Approval

Status: APPROVED
Approved by: Human request in this task authorizing implementation of the attached plan, local validation and merge to main.
Approved at: 2026-10-11 03:13 Asia/Taipei
Approval record: Explicit task request; scope is limited to the attached Skill-incubation recommendations and required AIPS review/documentation evidence.
Proposal fingerprint: Pending final exact-candidate review.
Scope fingerprint: Pending final exact-candidate review.
