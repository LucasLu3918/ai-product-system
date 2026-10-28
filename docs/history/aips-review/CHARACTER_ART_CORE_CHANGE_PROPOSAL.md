# Core Change Proposal: Local Character Art Workflow

## Purpose

Add a reusable, local-first character-art workflow to AIPS so agents can preserve character identity across generated assets, safely validate/provenance-track images, compose a character sheet with correctly typeset labels, and review visual quality separately from deterministic evidence.

## Why this is a core/large change

The change extends AIPS's shared creative workflow, image-input safety boundary, generated Skill projection, documentation, architecture diagrams, and validation lifecycle. It adds a new reusable artifact/validation flow across multiple runtime consumers.

## Proposed Scope

### In scope

- Extend existing `creative-calibration`, `visual-direction`, and `visual-quality-review` Skills; do not create a new Role, Capability, Skill, custom MCP server, or provider adapter.
- Add character identity and visual style profiles plus an artwork manifest containing format/dimensions, lineage hashes, provider/model/runtime/license, and optional measured performance fields.
- Add a deterministic helper for strict SVG/PNG inspection, project-confined paths, source-preserving atomic outputs, manifest validation, and SVG character-sheet composition with Chinese text labels.
- Document the official local Comfy MCP route and optional MFLUX route. No remote/cloud/partner provider is selected or executed by default.
- Add contract, negative-path, synthetic end-to-end, existing-flow compatibility, OpenCode projection, Scenario, documentation, and architecture coverage.

### Out of scope

- Paid image APIs, cloud generation, custom provider integrations, model downloads, or environment installation.
- Device-specific generation-quality or performance claims; those require an actual configured M5 Pro/MFLUX or ComfyUI run.
- Automatic visual PASS from file existence, image metadata, or deterministic tests.

## Expected Files / Modules

- `.aips/review/CHARACTER_ART_SYSTEM_IMPROVEMENT_REVIEW.md`
- `.aips/review/CHARACTER_ART_CORE_CHANGE_PROPOSAL.md`
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `templates/creative/CHARACTER_PROFILE.yaml`
- `templates/creative/STYLE_PROFILE.yaml`
- `templates/creative/CHARACTER_ARTWORK_MANIFEST.yaml`
- `templates/creative/CREATIVE_EVIDENCE.yaml`
- `scripts/character_artifacts.py`
- `scripts/creative_evidence.py`
- `skills/design/creative-calibration/SKILL.md`
- `skills/design/visual-direction/SKILL.md`
- `skills/design/visual-quality-review/SKILL.md`
- `skills/INDEX.yaml`
- `orchestration/CREATIVE_DIRECTION.md`
- `tests/evidence/character_artifacts_lifecycle.py`
- `tests/evidence/creative_render_lifecycle.py`
- `tests/validation/character_artifacts_contracts.py`
- `tests/validation/creative_evidence_contracts.py`
- `tests/validation/registry.py`
- `tests/scenarios/234-character-art-workflow.md`
- `docs/human/USER_GUIDE.md`
- `docs/human/CONFORMANCE.md`
- `docs/ARCHITECTURE.md`
- `docs/human/ARCHITECTURE_OVERVIEW.md`
- `docs/human/assets/system-overview.svg`
- `CHANGELOG.md`

## Impact

### Architecture / Contracts

Additive creative-art templates and a standalone deterministic helper. Keep current creative evidence API/CLI behavior and AIPS runtime adapters stable. The canonical Skill Index remains the source for OpenCode projection.

### Data / Migration

No persistent database, project migration, or model storage. Raw prompts are not stored by the helper. Existing user assets are input-only and cannot be overwritten.

### Security / Reliability

No automatic network egress. Local Comfy MCP/MFLUX is documented as an explicit user-configured execution path. Reject unsafe SVG features, absolute/traversal/symlink-escaping manifest paths, hash mismatches, unsupported formats, missing model-license provenance, and overwrite attempts. Missing runtime/model/performance evidence stays UNKNOWN. Deterministic validity never implies subjective visual quality.

### Compatibility / Rollback

No breaking API changes or migration. Existing creative evidence remains valid; new metadata is optional/additive. Rollback is a Git revert and removal of the new helper/templates; no model or user data is created.

### Tests / Validation

Impact-derived Test Matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Character/style profiles and artwork manifest | Required | Required | Required | Required | Synthetic fixture | Required | No persistent state | Standalone CLI lifecycle | Required | N/A only for database migration |
| SVG/PNG safety and sheet composition | Required | Required | Required | Required | Synthetic generated sheet | Required | Atomic no-overwrite recovery | Standalone CLI lifecycle | Required | N/A only for migration |
| Creative Skill routing and runtime projection | Required | Applicable | Required | Required | Provider execution unavailable in this environment | Explicit local-only / no-egress checks | No migration | OpenCode projection lifecycle | Required | Real image generation requires installed engine/weights |
| Existing Creative Evidence compatibility | Required | Required | Existing synthetic lifecycle | Required | Existing render lifecycle if browser can launch | Source hash preservation | No migration | No CLI surface change | Required | N/A only for migration |
| Human and architecture documentation | Required | Structural checks | VitePress build | Placement/sync checks | N/A | N/A | N/A | N/A | Required | No deployed product UI |

Recompute trigger if scope expands: new Skill/Capability/Role, AIPS CLI command, runtime-enforced provider invocation, remote provider/credential flow, non-SVG raster composer, persistent model/result storage, or actual model installation.

Required release/CI evidence: exact-candidate Core Integration Gate and required repository aggregate; GitHub CI provides independent browser/Node/runtime evidence.

### Secret / Credential Impact

Secrets required: NO

Approved acquisition mechanism: N/A

Leakage/redaction review: No credentials or raw prompts in committed artifacts or lifecycle output.

Rotation/revocation plan if exposure is found: N/A

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: AFFECTED — add local creative-art pipeline and independent visual-review boundary.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — describe local model execution and deterministic composition.
- `docs/human/assets/system-overview.svg`: AFFECTED — add the bounded creative-art workflow.
- `docs/human/assets/harness-overview.svg`: N/A — runtime adapter/projection topology does not change.
- `docs/human/assets/product-delivery-overview.svg`: N/A — no product delivery lifecycle changes.
- `docs/human/assets/project-intelligence-overview.svg`: N/A — Project Intelligence and Change Impact behavior do not change.
- `docs/human/assets/system-lifecycle.svg`: N/A — installation/project lifecycle does not change.

## Risks

Local inference speed and model support vary. Current toolchain documentation recommends cloud for large open-weight models on Mac; this scope excludes cloud/paid APIs and records performance only when measured. SVG content is active input and must be sanitized. The automated evidence can verify file integrity, not visual correctness.

## Recommendation

Proceed with existing Skill reuse, official local Comfy MCP guidance, optional MFLUX guidance, a deterministic safe artifact helper, and impact-derived tests. Defer model-weight downloads and actual M5 Pro benchmarks.

## Proposed Implementation Order

1. Bind this proposal and test matrix to the approved Change Impact boundary.
2. Add versioned character/style/artwork profiles and safe validation/composition helper.
3. Extend creative Skills, creative evidence provenance, and OpenCode projection coverage.
4. Add Scenario 234, human/agent guidance, architecture diagrams and Unreleased entry.
5. Run focused negative/compatibility tests, documentation gates, secret scan, exact-candidate Core Integration Gate, then prepare the Git Publish Proposal.

## Approval

Status: APPROVED
Approved by: Human user in this Codex task (`核准`).
Approved at: 2026-10-08 (Asia/Taipei).
Approval record: Current user turn after presentation of this proposal.
Proposal fingerprint: to bind after writing.
Scope fingerprint: AIPS Change Impact artifact `character-image-workflow-20261008`, scope approved after user reply `核准`.
