# Core Change Proposal: Dev Friction PR4 — Parameterized Local ComfyUI Generation

## Approved outcome

Move the remaining hard-coded ComfyUI sampler and prompt-upsampler values out of the topology validators into profile data, bounded by per-family ranges declared in the trusted registry and capped by executor-owned ceilings. Add optional per-profile runtime budgets so preflight warns or blocks before submission when a static estimate exceeds the effective timeout. Verify and narrowly fix the `OTHER_TASK` creative-admission false negative. Default ON; no trust-boundary change.

## Scope

- `templates/creative/COMFYUI_MODEL_PROFILES.yaml`: add `topology_families` (sampler ranges/enumerations per audited family; FLUX upsampler `max_length` range and default 1024); add `upsampler.max_length: 1024` to both FLUX 3 Klein profiles; document optional `runtime_budget` fields.
- `scripts/creative_execution.py`: load and validate families against executor ceilings (`steps` 1–100 integer, `cfg` 0–30, `denoise` 0–1, enum values `^[a-z0-9][a-z0-9_]{0,63}$` and at most 16, upsampler `max_length` 1–4096); profile values must fall inside family data; reject unknown profile keys and unknown families. The Z-Image validator compares the workflow sampler with profile values instead of literals; the FLUX validator compares TextGenerate `max_length` with the profile. Add `effective_timeout_seconds` (Bundle > profile > 900) and `comfy_runtime_estimate`; `verify_comfy` blocks with `comfy_runtime_budget_exceeded` before any ComfyUI request; preflight reports `runtime_budget`.
- `scripts/creative_errors.py`: allowlist the bounded numeric budget diagnostics and add a Traditional Chinese recovery for the new reason code.
- `scripts/creative_request_policy.py`: a website/email word no longer denies an explicit, non-negated image-deliverable request without code/data/login/deploy/send-email markers; such a request during a character continuation is a scope expansion.
- Tests: equivalence, variant, bound, budget and policy cases in `tests/evidence/creative_execution_lifecycle.py` and `tests/evidence/creative_request_policy_lifecycle.py`; Scenarios 236 and 238; one localized `docs/ARCHITECTURE.md` sentence.

## Why the security floor is not weakened

- `comfyui_workflow_policy.py`, `COMFY_CORE_NODES`, topology node classes, structure, links and fixed fields are unchanged. Registry data cannot add a family, node, operation, input image or endpoint (`operation` must stay `generate`; input-image nodes stay rejected for profiles).
- Loopback-only requests, no weight downloads and the single explicit submission are unchanged. Budget checks run before any request.
- The agent cannot switch models: the Bundle still names `model_profile`; budgets only warn/block and recommend a timeout, never select another profile.
- Diagnostics carry only bounded numbers and enums through the existing allowlist; no prompt, path or provider body.
- The admission fix applies only to OpenCode and is additionally gated by the plugin's Turn Context classification check.

## Defaults and equivalence

Existing profiles resolve to exactly the previous values (Z-Image Turbo: Bundle steps, CFG 1, res_multistep/simple, denoise 1; Klein Base 50/3.5; Distilled 16/1; FLUX upsampler 1024). No existing profile sets `runtime_budget`, so status is `UNESTIMATED` and the timeout remains the Bundle value or 900 seconds.

## Out of scope

Owned-job interruption (PR5), declarative topology templates and user-local profiles (PR6), edit models (D13), `turn_intent` classification changes, and calibrated runtime numbers for installed models.

## Human approval

- Core Change Approval: the human user approved the full dev-friction plan scope; this record applies it to exactly the PR4 scope above.
- Publication: not requested in this task; no push, PR or merge.
