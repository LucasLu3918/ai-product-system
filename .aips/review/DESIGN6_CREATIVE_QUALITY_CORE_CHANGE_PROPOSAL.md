# Core Change Proposal: Design6 Creative Quality Workflow

## Purpose

Close the gap between successful local image generation and delivery of artwork that reflects the selected Style Profile and stable Character Profile. Extend the existing AIPS creative executor and artifact workflow.

## Why this is a core change

The change spans creative request authorization, profile and bundle contracts, local model selection evidence, local visual review, provenance, OpenCode tooling, scenarios, and canonical documentation. It changes behavior across several runtime and privacy boundaries.

## Proposed Scope

### In scope

- Compile the existing Character, Style, Collection, and Bundle inputs into a deterministic model-ready prompt at execution time; preserve raw-prompt privacy and bind compiled prompt/profile fingerprints to provenance.
- Define a model capability profile and transparent, evidence-backed local model recommendations. Keep recommendations advisory; never install models or silently switch providers/models.
- Add an explicitly requested optional local vision-model review that returns structured findings only. Keep its status advisory and preserve separate Human visual review and user acceptance decisions.
- Extend shared collection style constraints, character identity acceptance fields, and character-artifact consistency checks while preserving existing profile compatibility.
- Expose the bounded review action through the existing OpenCode creative tool and authorization policy; preserve output-count limits and session-root confinement.
- Update affected creative scenarios, lifecycle evidence, canonical docs, documentation mapping, and changelog.

### Out of scope

- Downloading or installing model weights, runtimes, extensions, or model packages.
- Cloud image or vision APIs, external image egress, training/LoRA creation, or automatic model/provider changes.
- Automatic generation, retries, output-count increases, or replacing Human visual review / user acceptance with an AI decision.
- A new global creative framework, duplicate approval gate, role, or skill.
- Claims about actual model quality, device performance, or generated images without separately authorized local inference evidence.

## Expected Files / Modules

- Existing creative executor, request authorization policy, character-artifact validator, OpenCode adapter, creative profile templates, calibration/review skills.
- New model-capability profile and visual-review report schema.
- Existing creative lifecycle/scenario and documentation contracts; new quality lifecycle/contract evidence.
- Canonical Core Change Matrix, this proposal, the existing creative documentation surfaces, and `CHANGELOG.md`.

## Impact

### Architecture / Contracts

Add a deterministic profile-to-prompt compilation step before the existing local provider call. Add advisory model recommendation and visual-review outputs without changing provider allowlists, generated image output counts, or the meaning of `COMPLETE`, Human review, and user acceptance. New fields remain additive and older version-1 bundles remain readable.

### Data / Migration

No database or migration. Additive profile fields, provenance fingerprints, and a create-only structured review report. Reports contain no image bytes or raw prompts.

### Security / Reliability

Keep generation local-only and offline. Vision review is opt-in, fixed to a local loopback Ollama endpoint, uses installed-model inventory only, suppresses proxy use and redirects, and writes a bounded create-only report. AI findings cannot set Human review or user acceptance. Preserve authorization, project-root/path confinement, output ceilings, and no-overwrite behavior.

### Compatibility / Rollback

Existing profile and Bundle version 1 files remain accepted. The compiler derives additional provider input without rewriting saved prompts or existing assets. Rollback is a normal code revert; no durable service or schema migration is introduced.

### Tests / Validation

Impact-derived Test Matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Prompt compilation and provenance | REQUIRED | REQUIRED | REQUIRED | REQUIRED | N/A | REQUIRED | REQUIRED | REQUIRED | REQUIRED | No production UI/browser path; backward compatibility is exercised with existing version-1 fixtures. |
| Model profile and recommendation | REQUIRED | REQUIRED | REQUIRED | REQUIRED | N/A | REQUIRED | N/A | REQUIRED | REQUIRED | Recommendations use declared local evidence only; no model install or live inference in CI. |
| Optional local visual review | REQUIRED | REQUIRED | REQUIRED | REQUIRED | N/A | REQUIRED | REQUIRED | REQUIRED | REQUIRED | Mock only the fixed loopback API; actual VLM quality remains unverified. |
| OpenCode authorization/tool consumer | REQUIRED | REQUIRED | REQUIRED | REQUIRED | N/A | REQUIRED | N/A | REQUIRED | REQUIRED | Native host acceptance remains separately reported; tool harness covers current adapter contract. |
| Collection/profile/artifact compatibility | REQUIRED | REQUIRED | REQUIRED | REQUIRED | N/A | REQUIRED | REQUIRED | REQUIRED | REQUIRED | No persistent database; legacy profiles and deterministic sheet composition remain covered. |
| Canonical docs and scenarios | REQUIRED | N/A | REQUIRED | REQUIRED | N/A | REQUIRED | N/A | N/A | REQUIRED | Documentation sync, placement, scenario, and exact-candidate Gate contracts apply. |

Recompute trigger if scope expands: any provider/adapter addition, model installation or download, cloud/network destination, authorization or output-budget change, profile version bump, or new persistent state.

Required release/CI evidence: exact-candidate Core Integration Gate, candidate secret scan, creative lifecycle/contract evidence, documentation impact and placement PASS, plus PR `repository` check.

### Secret / Credential Impact

Secrets required: NO

Approved acquisition mechanism: N/A

Leakage/redaction review: verify raw prompts, images, VLM output, local paths, and credentials are absent from traces; report files remain local to the selected project.

Rotation/revocation plan if exposure is found: N/A; no credentials are introduced.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md` Mermaid: AFFECTED — update the creative pipeline to show Profile compilation, advisory model selection, optional local review, and the independent Human decision boundary.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — synchronize the existing Creative Workflow explanation.
- Human SVG architecture/lifecycle diagrams: N/A — no separate creative-specific SVG exists; the canonical Mermaid and overview are the maintained diagrams.

### Exact implementation target paths

- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- `.aips/review/DESIGN6_CREATIVE_QUALITY_CORE_CHANGE_PROPOSAL.md`
- `CHANGELOG.md`
- `config/documentation-placement.yaml`
- `config/documentation-sync.yaml`
- `docs/ARCHITECTURE.md`
- `docs/human/ARCHITECTURE_OVERVIEW.md`
- `docs/human/CONFORMANCE.md`
- `docs/human/DOCUMENTATION_MAP.md`
- `docs/human/DOCUMENTATION_SYNC.md`
- `docs/human/EVOLUTION_RADAR.md`
- `docs/human/HARNESS.md`
- `docs/human/INSTALLATION.md`
- `docs/human/MAINTENANCE.md`
- `docs/human/PROJECT_INTELLIGENCE.md`
- `docs/human/SECURITY_ASSURANCE.md`
- `docs/human/TECHNOLOGY_GUIDE.md`
- `docs/human/USER_GUIDE.md`
- `docs/human/index.md`
- `harness/HARNESS_PROTOCOL.md`
- `harness/adapters/opencode/AGENTS.md`
- `harness/adapters/opencode/COMPATIBILITY.md`
- `harness/adapters/opencode/plugin.ts`
- `orchestration/CHANGE_IMPACT.md`
- `orchestration/CONFORMANCE.md`
- `orchestration/CREATIVE_DIRECTION.md`
- `orchestration/DETERMINISTIC_SCHEDULER.md`
- `orchestration/DOCUMENTATION_SYNC.md`
- `orchestration/EXECUTION_ISOLATION.md`
- `orchestration/GITHUB_RULESET_POLICY.md`
- `orchestration/INTEGRATION_GATE.md`
- `orchestration/ORCHESTRATOR.md`
- `orchestration/PROJECT_INTELLIGENCE.md`
- `orchestration/RELEASE_READINESS.md`
- `orchestration/RUNTIME_CONTEXT.md`
- `scripts/aips_cli/dispatch.sh`
- `scripts/aips_cli/help.sh`
- `scripts/character_artifacts.py`
- `scripts/creative_execution.py`
- `scripts/creative_request_policy.py`
- `skills/design/creative-calibration/SKILL.md`
- `skills/design/visual-quality-review/SKILL.md`
- `templates/creative/CHARACTER_ARTWORK_MANIFEST.yaml`
- `templates/creative/CHARACTER_PROFILE.yaml`
- `templates/creative/CREATIVE_BUNDLE.yaml`
- `templates/creative/CREATIVE_COLLECTION_PROFILE.yaml`
- `templates/creative/MODEL_CAPABILITY_PROFILE.yaml`
- `templates/creative/STYLE_PROFILE.yaml`
- `templates/creative/VISUAL_REVIEW_REPORT.schema.json`
- `tests/evidence/character_artifacts_lifecycle.py`
- `tests/evidence/creative_execution_lifecycle.py`
- `tests/evidence/creative_quality_lifecycle.py`
- `tests/evidence/creative_request_policy_lifecycle.py`
- `tests/evidence/creative_tool_harness.mjs`
- `tests/fixtures/plan21-contract-golden-vectors.yaml`
- `tests/scenario_coverage.yaml`
- `tests/scenarios/234-character-art-workflow.md`
- `tests/scenarios/236-local-creative-execution.md`
- `tests/scenarios/238-creative-task-authorization-and-multi-item-execution.md`
- `tests/validation/creative_execution_contracts.py`
- `tests/validation/creative_quality_contracts.py`
- `tests/validation/registry.py`

## Risks

- Prompt compilation may improve instruction coverage but cannot guarantee visual correctness; report fingerprints and model evidence without claiming image quality.
- Local VLM findings can be wrong. They remain advisory and require independent Human inspection.
- The AIPS Impact Graph has partial consumer coverage; manually reviewed source/documentation mappings must remain explicit and global coverage must not be promoted.
- Full local Gate currently requires a prepared Python/Node environment and process capabilities that must be rechecked before candidate validation.

## Recommendation

Extend the narrowest existing creative abstractions. Do not add a new framework or make model-specific quality claims without measured evidence.

## Proposed Implementation Order

1. Add backward-compatible profile fields, model capability evidence, and deterministic prompt compilation.
2. Add the opt-in loopback visual-review report and keep its authority strictly advisory.
3. Extend collection/character consistency validation and expose review through existing OpenCode authorization.
4. Add lifecycle, contract, Scenario 234/236/238, documentation, and exact-candidate Core evidence.

## Approval

Status: APPROVED
Approved by: Human
Approved at: 2026-10-09T14:53:19Z
Approval record: User message `核准` in the current task, approving the four-stage Design6 System Improvement Review scope.
Proposal fingerprint: sha256:2858969e57588a78ab484afe12b01c5c0ff61846179925ba8ff876f1b959fe08 (SHA-256 over proposal with this field set to the pending placeholder)
Scope fingerprint: sha256:5eb0abaefb98e73919727a3097352a78044d4186c30179fc6bcaa287b12c0d27
