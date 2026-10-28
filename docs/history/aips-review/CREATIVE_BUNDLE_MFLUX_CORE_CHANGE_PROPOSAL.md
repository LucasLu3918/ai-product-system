# Core Change Proposal: Creative Bundle Preparation and MFLUX CLI Mapping

## Objective

Complete the existing local character-art workflow so a user can safely prepare a versioned Character Profile, Style Profile and Creative Bundle, then explicitly configure an already-installed local engine. Map supported MFLUX model/operation combinations to fixed executable names and argument shapes.

## Approved change boundary

- Add `aips creative prepare` and an OpenCode `creative_execution` prepare action that write fixed files only in an explicitly selected non-Git EPHEMERAL scope.
- Serialize concurrent preparation and never replace a versioned workspace or existing asset.
- Add a closed MFLUX CLI capability table for FLUX.1, FLUX.2 Klein and Qwen Image Edit 2511; FLUX.1 edit accepts one project-contained reference, while FLUX.2/Qwen edit accepts at most eight.
- Keep ComfyUI loopback-only, built-in-node-only and limited to one staged hash-matched edit reference.
- Preserve explicit preflight/execute, offline model behavior, local-only image bytes, provenance, pending human review and privacy-bounded traces.
- Update CLI/OpenCode contracts, Scenario 236, lifecycle evidence, canonical documentation and diagrams, documentation mapping, version and changelog.
- Do not download/install engines or weights, train models, call cloud image services, or alter Constitution semantics.

## Risk and compatibility

Risk class: `security_boundary`. The capability is additive: no data migration or breaking change is expected. Legacy single-input Bundles and existing FLUX.1 commands remain supported. Unknown models, operations or executable names fail closed. Real model quality/device performance are not claimed from synthetic tests.

## Architecture review

Updated: `docs/ARCHITECTURE.md` Runtime flow; `docs/human/ARCHITECTURE_OVERVIEW.md` OpenCode adapter description; `docs/human/assets/harness-overview.svg` OpenCode bounded-tool label.

Not affected: `docs/human/assets/system-overview.svg` (high-level access-plane diagram does not describe this workflow); `docs/human/assets/project-intelligence-overview.svg` (no Intelligence lifecycle change); `docs/human/assets/system-lifecycle.svg` (no install/update/workspace identity lifecycle change); product-delivery diagram (no delivery lifecycle change).

## Approval and evidence

- System Improvement Review: `.aips/review/CREATIVE_BUNDLE_MFLUX_SYSTEM_IMPROVEMENT_REVIEW.md`.
- Core Change Approval: user explicitly approved “上述完整範圍” on 2026-10-08 before implementation.
- Local synthetic evidence: `tests/evidence/creative_execution_lifecycle.py`, `tests/evidence/opencode_integration_lifecycle.py`, `tests/validation/creative_execution_contracts.py`, Scenario 236 and documentation placement.
- Exact-candidate Core Integration Gate and final Git-bound Impact reconciliation must pass before remote publication; neither grants merge authority.
- Remote publication requires a separate exact-candidate Git Publish Proposal approval.
