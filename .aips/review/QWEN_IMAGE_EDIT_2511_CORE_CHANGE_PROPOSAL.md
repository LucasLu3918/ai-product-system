# Core Change Proposal: Qwen Image Edit 2511 Dual-reference ComfyUI

## Problem and recommendation

The local dynamic ComfyUI binding contract currently allows multi-reference injection only for `TextEncodeQwenImage21.images`. Qwen Image Edit 2511's built-in `TextEncodeQwenImageEditPlus` exposes individual `image1`, `image2`, and `image3` ports, so the current validator rejects the exact two-reference workflow needed to retain separate identity and product conditioning.

Extend the existing ordered reference contract with one explicit Edit Plus mapping. Preserve the Qwen 2.1 object-map binding and all existing trust, schema, loopback, size, staged-hash, and recovery boundaries. This does not add a node, topology registry family, provider, endpoint, or operation.

## Scope

- Allow `reference_encoder.input: image1` only when the selected runtime core node is `TextEncodeQwenImageEditPlus`.
- Map the ordered `image_1..image_N` reference bindings onto contiguous `image1..imageN` node ports, with N capped at three.
- Preserve existing Qwen 2.1 behavior, eight-input bound for its object map, and `reference` single-image binding.
- Add positive and negative lifecycle cases, a static execution contract, Scenario 236 evidence, and concise canonical workflow guidance.
- Add a KOHAMI project-local model profile and API workflow after the system change; preflight against live local ComfyUI only.

## Out of scope

- Automatic model/profile selection, arbitrary topology registration, custom nodes, MFLUX model downloads, cloud execution, inference fallback, or changes to Human authorization.
- Real inference acceptance on Apple MPS; the change adds workflow support only.

## Security and compatibility

Only runtime-identified `comfy_extras` encoder nodes are eligible. The AIPS workflow still requires two distinct project-local `LoadImage` nodes, contiguous ordered bindings, safe staged filenames, exact staged-byte hash checks, installed local models, a loopback endpoint, one `SaveImage`, and one explicit submission. Existing Qwen 2.1 workflows continue emitting the same `images` map.

## Test matrix

See the active candidate-bound `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`. Architecture diagrams are unchanged because node/endpoint/trust boundaries remain the same; the data mapping is documented in text.

## Human approval

The proposal records user authorization to modify the local AIPS system and contract checks on 2026-10-26. The user explicitly authorized review of all PRs, creation of replacement PRs, and merging suitable changes into `main` on 2026-10-28; this PR is in scope only if review and required checks pass. Constitution impact: NO.
