# Eval / Red-Team Interoperability Core Change Proposal

## Purpose

Add a provider-neutral boundary for safely importing and exporting external Eval / red-team evidence while keeping AIPS `agent_eval`, deterministic verification, security governance, and Human publication authority canonical.

## Why this is a core/large change

The feature adds public evidence schemas, CLI behavior, external-input security rules, risk-based Eval profiles, scenario coverage, and documentation/architecture changes. A bad import or gate mapping could execute untrusted code, leak evidence, report a false PASS, or let a stochastic score influence release decisions.

## Proposed Scope

### In scope

- AIPS canonical external evidence and red-team finding contracts with provenance, source/license/digests, runner/target/scorer metadata, evidence class, status, and stale-result detection.
- Static, bounded, fail-closed Promptfoo config import; JSONL result normalization; AIPS Case/result export for an explicit built-in provider; no automatic Promptfoo execution.
- PyRIT pilot bridge contract and result adapter with no PyRIT runtime dependency; bridge inputs remain untrusted.
- Hard gate eligibility for verified deterministic canonical regression only; LLM judging and discovery scans are REVIEW/SIGNAL by default; unexecuted or failed runs cannot become PASS.
- Risk-profile selection for ordinary changes, prompt/system changes, routing/tool policy, RAG, MCP/tool permission, credential/SAL3-4, provider migration, release candidates, and optional deep PyRIT.
- Human-confirmed Finding → minimal reproduction → canonical regression promotion workflow.
- CLI, tests, schemas, fixtures, Scenario registration, architecture and canonical documentation. Preserve runtime Content Safety and Runtime Policy Enforcement as separate enforcement boundaries.

### Out of scope

- Running promptfoo or PyRIT inside AIPS core CI, installing either framework as a required dependency, or requiring external model/API credentials.
- Executing user-imported JavaScript, Python, shell, webhook, file-backed providers, test generators, extensions, hooks, or unknown assertions.
- Enabling remote generation, sharing, telemetry, or upload by default; granting external runner results release authority.
- Direct garak or DeepTeam adapters in this increment; revisit only if promptfoo/PyRIT pilot evidence identifies an unmet need.
- Changing the Constitution, Runtime Policy Enforcement, Content Safety enforcement, deployment, or autonomous PR/merge authority.

## Expected Files / Modules

- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` and this proposal.
- `VERSION`, `CHANGELOG.md`, `bin/aips`, `config/eval-profiles.yaml`, `config/architecture-surfaces.yaml`, `config/documentation-sync.yaml`, `config/documentation-placement.yaml`.
- `scripts/eval_interop.py`; external Eval, Eval profile, and red-team finding schemas under `orchestration/schemas/`.
- `orchestration/EVAL_INTEROPERABILITY.md`, updates to `AGENT_EVAL.md`, `CONFORMANCE.md`, and `INTEGRATION_GATE.md`.
- Focused fixtures, unit/lifecycle/contract validation, Scenario `180` (Scenario 179 was added by the prerequisite core Change Impact merge), and `tests/scenario_coverage.yaml` registration.
- `docs/ARCHITECTURE.md`, Human Architecture Overview, Conformance, Security Assurance, User Guide, Technology Guide / Maintenance / Documentation Map as required by documentation impact; update the affected system-overview SVG and record system-lifecycle.svg as N/A.

Exact changed paths are reconciled against the approved Change Impact and documentation closure after implementation.

## Impact

### Architecture / Contracts

External Eval producers feed a static parser and AIPS normalizer; normalized evidence is fingerprinted and verified by existing deterministic contracts. Promptfoo format is an adapter target, not the canonical AIPS format. PyRIT is a second pilot adapter. The architecture diagram must show the evidence-producer / normalizer / AIPS-governance path.

### Data / Migration

Additive schemas and config only; no existing Case/Result migration. Existing Agent Eval remains offline compatible. External evidence is opt-in and may contain sensitive prompts/responses; reject private reasoning and secret-like content before durable output.

### Security / Reliability

Use duplicate-key rejecting YAML parsing, reject YAML aliases/custom tags, bound bytes/items/depth, permit only documented inline deterministic fields, reject executable paths/providers/hooks and unknown assertions, validate hashes and provenance, and fail closed on incomplete evidence. LLM-as-a-Judge and generated attacks remain advisory.

### Compatibility / Rollback

No third-party runtime dependency and no change to existing Case/Result schema. The new CLI and optional profile config can be removed without migrating existing evidence. If repository validation or consumers reveal incompatibility, revert the feature commit; do not rewrite old fingerprints.

### Tests / Validation

Impact-derived Test Matrix: `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`.

Recompute trigger if scope expands: any change to runtime enforcement, Core Integration Gate authority, existing Case/Result semantics, external execution, workflow credentials, or storage/migration.

Required release/CI evidence: focused unit and end-to-end lifecycle tests; negative security inputs; promptfoo JSONL and PyRIT bridge fixture round trips; deterministic AIPS rescore; Scenario/Conformance; repository validation; documentation and architecture validation; exact-candidate Integration Gate and required repository aggregate CI.

### Secret / Credential Impact

Secrets required: NO.

Approved acquisition mechanism: N/A. Promptfoo/PyRIT are not executed by this change.

Leakage/redaction review: exercise secret-like and private-reasoning rejection on imported config, results, finding, and bridge inputs; diagnostics must include paths/categories only.

Rotation/revocation plan if exposure is found: stop publication, revoke/rotate externally exposed credential, purge affected artifact according to existing policy, and rerun secret scan.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: AFFECTED — add external evidence producer / normalization data flow.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — explain external Eval adapters and authority boundary.
- `docs/human/assets/system-overview.svg`: AFFECTED — align the visible Eval / evidence flow with Mermaid.
- `docs/human/assets/system-lifecycle.svg`: N/A — this diagram describes install, workspace persistence and isolation lifecycle; this feature adds no behavior to those flows.

## Risks

- Promptfoo and PyRIT formats evolve; pin the supported subset/version and reject unsupported shapes rather than guessing.
- Importing raw external observations can expose sensitive prompts/results; secret and private-reasoning checks must happen before output.
- External tool PASS values are not authoritative; do not use raw score/status as a release decision.
- AIPS Impact Graph lacks Eval relationships; retain graph traversal as unknown and use direct source/consumer evidence until the graph is enriched.

## Recommendation

Implement the complete plan7 scope as one bounded optional interoperability feature on AIPS v0.64.0. Preserve the canonical AIPS contracts and make Promptfoo and PyRIT adapters producer-only. Do not add mandatory external dependencies or runtime execution.

## Proposed Implementation Order

1. Add schema, safe parser/normalizer, canonical fingerprints, deterministic import/export, and offline tests.
2. Add explicit Promptfoo export/import; verify against current official config and JSONL shape.
3. Add PyRIT bridge pilot, finding promotion, and risk-profile selection.
4. Add CLI, Scenario/lifecycle coverage, Integration Gate policy documentation, architecture and Human documentation.
5. Run documentation impact, security review, full affected-boundary matrix, exact candidate preflight, and CI.

## Approval

Status: APPROVED
Approved by: User (explicit request to implement all plan7 recommendations and merge the PR to main)
Approved at: 2026-09-26 (Asia/Taipei)
Approval record: Current user message, following `/Users/lucas/Coding/main/plan7.md`
Proposal fingerprint: pending final content hash
Scope fingerprint: pending final boundary hash
