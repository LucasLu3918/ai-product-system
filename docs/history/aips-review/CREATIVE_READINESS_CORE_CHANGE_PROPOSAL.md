# Core Change Proposal: Local Creative Readiness and Diagnostics

## Purpose

Close the remaining gaps identified in the design5 review: the OpenCode configure schema omits fields already accepted by the shared executor, engine discovery conflates command/version states and does not inspect the supported loopback ComfyUI endpoint, and Apple Silicon dtype compatibility is always reported as unverified without actionable static warnings.

## Why this is a core/large change

The change updates an OpenCode tool contract, local provider discovery/preflight, safety-sensitive execution diagnostics, and the creative lifecycle evidence and canonical guidance. Exact caller/consumer traversal is recorded in the external EPHEMERAL Project Intelligence scope `creative-execution-local-pipeline`; repository-wide graph coverage remains partial.

## Approved Scope

### In scope

- Add optional `model_profile`, `unet_name`, `clip_name`, and `vae_name` fields to the OpenCode ComfyUI configure schema, matching the executor's allowlist and preserving `additionalProperties: false`.
- Make MFLUX discovery distinguish command presence from an unverified/failed version probe; never infer model readiness or inference from `--version`.
- Add bounded, read-only discovery for only `http://127.0.0.1:8188`, using `/system_stats` and `/object_info`, with categorized service/model/workflow outcomes. Do not probe arbitrary configured URLs during general discovery.
- Add staged readiness fields for command, runtime, model, preflight, and inference. Keep inference `UNVERIFIED` until a real generation result exists.
- Detect explicit FP8 dtype/filename evidence on Apple Silicon and report a static compatibility warning with a safer precision suggestion. Do not claim all FP8 models are incompatible, block solely on filename heuristics, modify ComfyUI/PyTorch, or claim inference compatibility.
- Preserve `creative generate-set` for partial success and hash-verified resume. Extend the existing deterministic lifecycle and contract checks; do not add a duplicate batch command, Role, Skill, or Capability.
- Update Scenario 236, the user guide, architecture descriptions, conformance, changelog and version metadata as required by the final documentation-impact closure.
- After the PR Gate exposed that GitHub subprocess fixtures did not inherit the installed full Python 3.12 interpreter, export `AIPS_VALIDATION_PYTHON` in the validation workflow and lock this handoff with a workflow contract regression.

### Out of scope

- Running real MFLUX/ComfyUI inference, creating Harry/Hermione images, model downloads, and hardware performance or visual-quality claims. These remain separate explicit local validation actions.
- New image providers, remote/LAN ComfyUI, external image APIs, custom nodes, arbitrary command templates, changes to creative authorization, or modifications to ComfyUI/PyTorch source.
- Constitution, branch protection, merge policy, persistent prompt retention, or user data migration.

## Expected Files / Modules

Exact final candidate file set (35 paths):

```text
.aips/review/CORE_CHANGE_TEST_MATRIX.yaml
.aips/review/CREATIVE_READINESS_CORE_CHANGE_PROPOSAL.md
.aips/review/CREATIVE_READINESS_SYSTEM_IMPROVEMENT_REVIEW.md
.github/workflows/validate.yml
CHANGELOG.md
VERSION
docs/ARCHITECTURE.md
docs/human/ARCHITECTURE_OVERVIEW.md
docs/human/CONFORMANCE.md
docs/human/DOCUMENTATION_MAP.md
docs/human/DOCUMENTATION_SYNC.md
docs/human/HARNESS.md
docs/human/INSTALLATION.md
docs/human/MAINTENANCE.md
docs/human/SECURITY_ASSURANCE.md
docs/human/TECHNOLOGY_GUIDE.md
docs/human/USER_GUIDE.md
docs/human/index.md
harness/HARNESS_PROTOCOL.md
harness/adapters/opencode/AGENTS.md
harness/adapters/opencode/COMPATIBILITY.md
harness/adapters/opencode/plugin.ts
orchestration/CONFORMANCE.md
orchestration/CORE_CHANGE_TESTING.md
orchestration/CREATIVE_DIRECTION.md
orchestration/DETERMINISTIC_SCHEDULER.md
orchestration/DOCUMENTATION_SYNC.md
orchestration/INTEGRATION_GATE.md
orchestration/ORCHESTRATOR.md
scripts/creative_execution.py
tests/evidence/creative_execution_lifecycle.py
tests/evidence/creative_tool_harness.mjs
tests/scenarios/236-local-creative-execution.md
tests/validation/creative_execution_contracts.py
tests/validation/publish_preflight_contracts.py
```

The active matrix binds the final reconciled list to base `7463a0a3cd08c9578b007518d1d544bb4434b625`; its candidate hash is refreshed by `aips publish matrix-sync` after the final commit.

## Impact

### Architecture / Contracts

The native OpenCode schema becomes consistent with the existing executor's optional ComfyUI Z-Image Turbo profile. Discovery adds an allowlisted loopback GET-only probe and additive status fields. Existing Bundle v1, CLI actions, provider selection, `generate-set`, reason codes, output manifest and trace contracts remain compatible.

### Data / Migration

No durable user data, migration or persistent prompt data. Discovery output is transient. Existing manifest and trace remain backward compatible.

### Security / Reliability

General discovery contacts only loopback port 8188, with bounded response sizes/timeouts, no credentials, redirects, proxy use or writes. It never downloads weights or submits a workflow. MFLUX discovery stays within the fixed command registry and runs only the bounded version probe. Diagnostic paths, prompts and secrets are not emitted. Unknown dtype/model metadata stays `UNVERIFIED`.

### Compatibility / Rollback

Schema fields and result diagnostics are additive. Existing workflow and Bundle formats remain supported. Reverting the candidate restores previous diagnostics without data migration.

### Tests / Validation

| Affected boundary | Required evidence |
|---|---|
| OpenCode configure schema | Contract asserts schema/executor allowlist parity for all Z-Image Turbo fields and rejects unknown fields. |
| MFLUX discovery | Fake commands for missing executable, nonzero/timeout/empty version, and successful version; command presence remains distinct from runtime/model readiness. |
| ComfyUI discovery | Loopback fixture for reachable/unreachable service, malformed responses and model inventory; prove only fixed localhost URL is contacted and no workflow is submitted. |
| Apple Silicon compatibility | Deterministic dtype/name cases for FP8 warning, FP16/BF16 suggestion and unknown dtype; inference remains unverified. |
| Creative workflow | Existing multi-item recovery lifecycle plus execution lifecycle, privacy/no-download/no-overwrite assertions. |
| Documentation / publication | Scenario and canonical docs sync, generated projection check if applicable, strict candidate/history secret scan, and exact-candidate local Integration Gate. The AIPS placement/sync rules also require Security Assurance and the relevant CI/Core Gate protocol pages in the recursive closure. |
| CI validation interpreter | Workflow contract proves the fully provisioned Python interpreter is exported before the deterministic Gate so isolated CLI fixtures use the installed Python 3.12 dependencies. |

Real model inference, runtime-specific OpenCode host acceptance and visual review remain separately reported as `UNVERIFIED` when unavailable; fixture evidence cannot satisfy them.

## Local Validation State

- Worktree `bin/aips validate`: PASS on Python 3.12.14; all repository lifecycle contracts passed (`0.80.0`, 12 roles, 27 skills, 238 scenarios).
- Creative execution and generate-set synthetic lifecycles: PASS, including fixed-loopback service discovery, no workflow submission during discovery, FP8/FP16/BF16/unknown precision behavior, OpenCode schema parity and provider-specific recovery.
- Documentation placement: pending final 35-path exact-candidate closure. Capability projection: PASS (45 capabilities, 10 surfaces).
- Exact-candidate Integration Gate / VitePress build: rerun required after the approved workflow and regression additions; reports are kept outside the repository to avoid self-reference.
- Real model inference, hardware performance and independent visual quality: UNVERIFIED and outside this approved scope.

### Secret / Credential Impact

Secrets required: NO. No credential acquisition. Diagnostics use allowlisted statuses and never include raw prompt, image, local model path or provider output.

### Documentation / Diagrams

- `docs/ARCHITECTURE.md`: AFFECTED — local discovery/readiness states in existing creative pipeline.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: AFFECTED — clarify staged engine/model/inference evidence.
- Human SVG architecture/lifecycle diagrams: N/A — no new provider or workflow boundary; re-evaluate against final diff.

## Risks

- A loopback service could be unrelated to ComfyUI; require both endpoints and classify malformed responses as `UNVERIFIED`/unavailable without sending sensitive data.
- Filename/dtype metadata can be incomplete; emit advisory warnings only and keep unsupported/unknown facts explicit.
- Host restrictions or missing pinned validation dependencies may prevent the local Integration Gate; such evidence must remain blocked rather than inferred green.

## Recommendation

Approve this narrow extension of the existing creative executor and OpenCode adapter. Reuse current `generate-set`, Profiles, manifests, trace, and human review boundaries.

## Proposed Implementation Order

1. Add the approved scope to Change Impact and bind the active Core Change Matrix.
2. Align the OpenCode configure schema with the executor and add a parity regression.
3. Refine MFLUX and fixed-loopback ComfyUI discovery, recovery codes and staged readiness output.
4. Add conservative Apple Silicon dtype warnings and deterministic negative/unknown cases.
5. Update Scenario 236, canonical docs, changelog and version; recompute Change Impact.
6. Run focused checks, prepare the Python 3.12 local toolchain where possible, then run the exact-candidate Core Integration Gate and publication proposal.

## Approval

Status: APPROVED
Approved by: Human user in the current Codex task
Approved at: 2026-10-09 (Asia/Taipei)
Approval record: User approved the design5 scope, fixed dependency installation in an isolated temporary environment, and the validate workflow Python interpreter handoff with a regression contract in this Codex task.
Proposal fingerprint: pending exact-candidate calculation
Scope fingerprint: pending final changed-file reconciliation
