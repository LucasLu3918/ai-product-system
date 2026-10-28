# FLUX 3 Klein Distilled and Multi-reference System Improvement Review

## Recommendation

**Appropriateness: appropriate.** The existing ComfyUI executor already supports reviewed data-only profiles and project-confined local references, but FLUX Klein sampler values were hard-coded to Base and dynamic ComfyUI edit bindings were fixed to one or two image slots. This prevented use of the available Distilled workflow and blocked larger reference sets despite the existing eight-image resource bound.

**Recommended design:** reuse the audited FLUX Klein T2I topology for Base and Distilled, move sampler values into each profile, validate those values against a bounded family contract, and keep live `/object_info`, local component inventory and final-payload checks. Generalize dynamic reference bindings to contiguous `image_1..image_N` slots up to eight and hash-check every staged input.

**Lower-layer alternative:** register Distilled as a profile on the existing topology rather than adding a new runtime, node family, capability or model router. This is the smallest reusable extension.

**Security and reliability:** model declarations do not add nodes, operations, endpoints or permissions. The loopback-only boundary, runtime core-node classification, safe filenames, per-file 12 MiB cap, aggregate 25 MiB cap, staged-source SHA-256 equality, create-only output and single explicit submission remain in force. The profile is not considered hardware or inference certified by preflight.

**Compatibility:** Base retains 50 steps / CFG 3.5; Distilled uses 16 steps / CFG 1. Z-Image keeps its existing explicit-step behavior. Existing one-reference dynamic bindings remain valid. The reference maximum remains eight.

**Scenario/test impact:** extend Scenario 236 and the local lifecycle with multi-reference ordered injection, over-limit rejection, invalid sampler rejection, and Distilled preflight/execution through the synthetic loopback service. No actual generation or weight installation is part of this change.

**Documentation impact:** AIPS publication preview requires 23 existing canonical documents to be synchronized. The user explicitly approved this additional documentation scope on 2026-10-26.

**Architecture diagrams:** no dataflow or trust-boundary diagram changes; the existing loopback ComfyUI boundary and executor path are unchanged.

**Constitution impact: NO.** Human authority, project precedence, security boundaries, scope integrity, publication authority and constitutional rules do not change.

**Additional optimizations:** defer any expansion beyond the existing eight-reference safety/resource bound and any new topology families. Automatic profile validation is included within the audited topology; arbitrary model/node registration is not.
