# Dev Friction PR4 System Improvement Review

## Recommendation

**Appropriateness: appropriate.** A same-family ComfyUI variant (for example FLUX 3 Klein Base with fewer steps or a 48-token prompt upsampler instead of 1024) required an executor code change because the Z-Image validator compared sampler literals and the FLUX validator fixed TextGenerate `max_length` at 1024. Long jobs were discovered only after submission when the 900-second timeout expired.

**Recommended design:** keep topology identity (node classes, structure, links, fixed fields, CLIP type) in the executor, and move only value ranges into registry data (`topology_families`) that may narrow, never widen, executor ceilings. Profiles carry their own sampler and upsampler values plus an optional static `runtime_budget`; preflight and execute evaluate it before any ComfyUI request.

**Lower-layer alternative:** the existing data-only profile mechanism was extended rather than adding a new runtime, router, capability or Skill. PR6 can later move topology structure into templates on top of this.

**Security and reliability:** the node trust policy, core-node allowlist, loopback-only requests, no-download rule, no input-image nodes for profiles, one explicit submission and final-payload validation are unchanged. Registry data cannot register a topology family, node, field, operation or endpoint; unknown profile keys are now rejected. Budget diagnostics are numeric/enumerated and pass the existing allowlist. The budget never selects another model.

**Compatibility:** existing profiles resolve to identical values (equivalence tests). Without `runtime_budget` the status is `UNESTIMATED`, and the timeout stays the explicit Bundle value or 900 seconds. A profile timeout applies only when a Bundle omits `timeout_seconds`; the shipped Bundle template sets 900 explicitly, so the main operational effect is the pre-submission `comfy_runtime_budget_exceeded` block with `recommended_timeout_seconds`.

**OTHER_TASK finding:** `scripts/creative_request_policy.py` is invoked only by `harness/adapters/opencode/plugin.ts`; no Claude Code, Codex, Gemini CLI, MCP or CLI path calls it. The fix therefore affects OpenCode only. In OpenCode the plugin also requires Turn Context `turn_intent` classification (`domain: creative`, `intent: create|modify`) for prepare/configure/execute, so prompts that `turn_intent` misclassifies (`幫網站做一張封面圖` → general/discuss, `幫我的網站生成一張封面圖` → software/create) remain blocked end to end; that root cause is outside PR4.

**Scenario/test impact:** Scenario 236 (profile values, family bounds, runtime budget) and Scenario 238 (website/email image destinations) updated; lifecycle evidence extended. No real ComfyUI job, weight install or inference.

**Documentation impact:** one localized sentence in `docs/ARCHITECTURE.md`; other canonical docs are left to the integration branch's documentation-impact closure.

**Architecture diagrams:** no dataflow or trust-boundary change.

**Constitution impact: NO.**

**Additional optimizations (deferred):** calibrated `runtime_budget` numbers from real local runs; a `turn_intent` creative-destination fix shared by all runtimes; PR5 owned-job interruption.
