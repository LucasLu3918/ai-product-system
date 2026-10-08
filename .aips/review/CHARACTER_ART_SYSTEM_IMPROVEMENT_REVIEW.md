# System Improvement Review: Character Art Workflow

## User Problem

AIPS can plan and review visual work, but it has no reusable character identity profile, local image-generation workflow, character-sheet composition contract, or image-asset provenance checks. The desired outcome is a local-first workflow that can turn user-owned character references into consistent, reviewable character artwork and a correctly typeset character sheet.

## Proposed Solution

Use the official local Comfy MCP for ComfyUI execution, retain MFLUX as an optional Apple Silicon route, and add character/style profiles, image provenance, deterministic sheet composition, SVG/PNG validation, and cross-runtime guidance.

## Appropriateness

Partially suitable. The problem is real and fits AIPS's reusable creative workflow. Provider-specific execution and real model performance remain environment-specific and must not be represented as verified by schema or fixture tests.

## Existing Coverage

- `creative-calibration` captures visual direction and reference aspects.
- `visual-direction` carries approved visual rules into design.
- `visual-quality-review` performs independent evidence-backed visual review.
- `CREATIVE_DIRECTION.yaml`, `CREATIVE_EVIDENCE.yaml`, `creative_evidence.py`, and the canonical OpenCode Skill projection cover direction, evidence integrity, and runtime reuse.

These cover general visual work, but not character identity, model/runtime provenance, image-file safety, or character-sheet assembly.

## Reuse / Extension Candidates

Extend the three existing design Skills, Creative Direction protocol, Creative Evidence schema/validator, and canonical Skill projection. Add narrow profile/manifest templates and a deterministic helper. Do not add a new Role, Capability, MCP server, or image-provider adapter.

## Lower-Layer Alternative

Keep model execution in the user's local ComfyUI/MFLUX installation and official Comfy MCP. AIPS owns reusable specifications, safe workflow guidance, deterministic validation, and evidence—not model execution infrastructure.

## Context / Token Cost

Bootstrap cost: none; existing creative capability remains the entry point.
Per-turn cost: low; image workflow guidance loads only for relevant requests.
On-demand cost: medium; character/style/profile schemas are loaded for character-art requests.
Mitigation: extend existing Skills and use compact templates; keep engine/model instructions as references.

## Security / Reliability

Security boundary impact: user-owned images and local filesystem paths; SVG is untrusted input.
Reliability/failure-mode impact: model availability and quality are external/local-runtime facts; schema and fixture success cannot imply successful generation.
Secret/persistence/concurrency/recovery impact: no credentials or raw prompts persisted; no automatic cloud/partner API, model download, or source overwrite; helper writes outputs atomically and confines inputs to the project root.

## Backward Compatibility

Compatibility: additive; existing creative evidence fields and AIPS CLI remain stable.
Migration required: no.
Existing runtime/project behavior affected: only agents choosing the character-art workflow; other creative work is unchanged.

## Scenario / Test Impact

Existing scenarios affected: 021, 022, and visual-review scenarios remain compatible.
New/updated scenario evidence: add Scenario 234 for local character-art planning, image safety/provenance, model/tool unavailability, and sheet composition.
Other applicable test evidence: deterministic synthetic SVG/PNG lifecycle; negative path-traversal, unsafe-SVG, stale-hash, missing-license, existing-output and malformed-image cases; current creative-evidence and OpenCode projection validators.

## Human Docs Impact

Affected: `docs/human/USER_GUIDE.md`, `docs/human/CONFORMANCE.md`, architecture overview, and system-overview diagram.
N/A reason: no deployment, pricing, or user-account workflow is introduced.

## Agent Docs Impact

Affected: three existing design Skills and `orchestration/CREATIVE_DIRECTION.md`.
N/A reason: no new Role or Skill is justified.

## Architecture Diagram Impact

Affected: `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, `docs/human/assets/system-overview.svg` show the Creative Workflow and its local image-tool, deterministic composition, and separate visual-review boundaries.
N/A: Harness overview (runtime projection mechanism is unchanged), Product Delivery overview, Project Intelligence overview, and System Lifecycle diagram (no corresponding lifecycle change).

## Constitution Impact

NO.

Why: no change to Human Authority, safety, stop-the-line, scope integrity, or constitutional amendment rules. Runtime MCP use remains explicitly user-directed and cannot grant remote publication authority.

## Recommended AIPS Solution

Extend existing creative guidance and review contracts; add character/style profiles, a provenance-bound artwork manifest, safe deterministic SVG sheet composition and SVG/PNG validation. Reuse the official Comfy local MCP. Describe MFLUX as an optional local execution path. Never infer model license/performance or visual quality from a manifest or a successful deterministic test.

## Additional Optimization Candidates

Candidate: install local models and benchmark FLUX.2 Klein / Z-Image on the user's exact M5 Pro hardware.
Benefit: empirical quality, latency, and peak-memory data.
Recommended timing: LATER.
Scope impact: large model downloads, external package/model registries, device-specific runtime and image-quality review.
Affected files/components: model store, ComfyUI/MFLUX installation, local hardware, generated test assets.
Status: DEFERRED.

## Expected Scope

### In scope

- Extend existing Creative Calibration, Visual Direction, and Visual Quality Review.
- Add reusable character/style profiles and a versioned artwork/provenance manifest.
- Add a deterministic local helper to validate image inputs and compose an SVG character sheet with accurate Chinese labels.
- Document official local Comfy MCP setup and optional MFLUX execution, with explicit local-only/no-egress defaults.
- Add negative-path, compatibility, Scenario, OpenCode projection, documentation, and architecture evidence.

### Out of scope

- Custom image model, MCP server, provider adapter, or paid/cloud image generation.
- Automatic ComfyUI/MFLUX/model installation or model-weight downloads.
- Claims of real M5 Pro generation speed, image quality, or peak memory without a device-bound run.
- Replacing human visual quality review with deterministic file checks.

## Risks

ComfyUI/MFLUX versions and installed models differ by workstation; generation may be slow or unavailable. SVG content can carry active/external references, so input parsing must be strict. A generated image can be structurally valid while visually inconsistent, which remains a separate review decision.

## Approval

Status: APPROVED
Approved direction: Extend existing AIPS creative capabilities for a local-first character-art workflow as described above.
Approved additional optimizations: none; hardware benchmarking and model downloads are deferred.
Deferred optimizations: exact-device model installation and benchmark.
Approved by: Human user in this Codex task (`核准`).
Approved at: 2026-10-08 (Asia/Taipei).
Approval record: current user turn after the Core Change Proposal.
