# Core Change Proposal: FLUX 3 Klein Distilled and Multi-reference ComfyUI

## Approved outcome

Support FLUX 3 Klein Distilled on the existing audited Klein topology and allow dynamic ComfyUI edit workflows to use an ordered variable number of references up to the established eight-image bound. Keep later profile additions data-only only within that audited family and validate every profile automatically; do not remove runtime schema, inventory, workflow topology or safety checks.

## Scope

- Replace the Base-specific topology identifier with a shared FLUX Klein topology identifier.
- Register Distilled with 16 steps, CFG 1, Euler/simple, denoise 1 and its exact local component filenames; preserve Base at 50 steps and CFG 3.5.
- Validate profile sampler fields and ranges centrally so future models within this topology need no executor edit while remaining constrained by live runtime validation.
- Generalize dynamic edit bindings to contiguous, ordered `image_1` through `image_N` references, where `1 <= N <= 8`.
- Preserve legacy single-reference `reference` bindings, model and node restrictions, project path confinement, size caps, hash matching, loopback-only requests, and one explicit submission.
- Update Scenario 236, the Core Change Test Matrix, the review record, and the 23 documentation paths required by publication preview.
- Verify on a feature branch, push the branch and create a PR after all gates pass. Do not merge or push protected `main`.

## Acceptance evidence

- Lifecycle accepts three ordered references, rejects a reference count over eight, and preserves the existing single-reference flow.
- Distilled profile passes local schema and model-inventory preflight, then the synthetic local execution uses 16 steps / CFG 1.
- Base remains 50 steps / CFG 3.5; Z-Image remains compatible.
- Documentation impact and placement report no missing required additions; Scenario 236 and the matrix describe the final diff.
- The exact committed candidate passes the AIPS Integration Gate, publication preflight, secret scan and approved Git identity checks.

## Constraints and limitations

No model weights are installed or downloaded, no real image is generated, and no claim is made about device compatibility, license acceptability or real inference quality. Profile data cannot register new nodes, topology families, operations, or external endpoints. The existing eight-file and byte limits remain in effect.

## Human approval

- Core Change proposal: approved by the user in this conversation (`核准`).
- Publication documentation closure (23 required existing documents): separately approved by the user in this conversation on 2026-10-26.
- Push authorization: user requested completion and approved push; create a reviewable feature branch/PR only. Merge remains outside scope.
