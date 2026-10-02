# Implementation Resolution Phase 3 System Improvement Review

**Appropriateness:** Conditionally appropriate. Phase 1 records ownership and quality intent, and Phase 2 binds OpenAPI evidence, but neither proves that a candidate still matches those declarations.

**User problem:** Generated files, selected language guidance, required project checks, and contract evidence can drift after an Implementation Profile is assembled. A structurally valid Profile can otherwise be mistaken for verified implementation readiness.

**Proposed solution:** Deterministic ownership, provenance, Profile fingerprint, language, quality-evidence, command, contract-drift and reproducibility checks, integrated with the existing Integration Gate.

**Existing coverage:** `implementation_profile_validate.py` validates Profile structure and exact ownership overlap; `openapi_contracts.py` validates and verifies revision-bound REST/OpenAPI evidence; `integration_gate.py` runs scoped candidate checks. None validates the complete Phase 3 handoff.

**Reuse / extension candidates:** Extend those three tools and the existing Implementation Profile. Keep command execution an explicit local action; the Gate verifies evidence and never executes a command supplied by an unreviewed Profile.

**Lower-layer alternative:** Individual projects can run their own build and tests. AIPS only needs a reusable evidence contract and deterministic verifier, while the project remains the authority for commands and assertions.

**Context / token cost:** The new contract and report are loaded only for applicable Implementation Resolution work. Other projects and unrelated changes retain their existing Gate path.

**Security / reliability:** Repository-relative paths must remain inside the checkout after symlink resolution. Unknown ownership is protected. Generated-output records bind output and input hashes but do not claim a generator was rerun. Explicit command execution uses argv, a timeout and digest-only output. Missing, stale or ambiguous evidence cannot pass enforcement.

**Backward compatibility:** Existing schema-v1 Profiles remain readable. The Phase 3 section is additive and disabled unless selected for a task. Existing Integration Gate profiles remain valid without a Phase 3 policy.

**Scenario / test impact:** Cover generated output edits and stale inputs, unclassified paths, language mismatch, missing or failed required checks, stale Profile/contract evidence, command timeout, same-input report stability and unaffected Gate paths.

**Human docs impact:** Update User Guide, Conformance, Security Assurance, Architecture Overview, Technology Guide and maintenance guidance.

**Agent docs impact:** Update Implementation Resolution, Integration Gate, Core Change Testing, documentation sync and routing references.

**Architecture diagram impact: YES.** Extend the existing Implementation Resolution evidence flow in `docs/ARCHITECTURE.md`; no deployment topology changes.

**Constitution impact: NO.** Human authority, contract approval and protected boundaries remain unchanged.

**Recommended AIPS solution:** A scoped Phase 3 verifier with a versioned evidence report, explicit command evidence and an optional existing-Gate policy. Report mode supports assessment; enforcement is enabled only for a configured Profile and affected paths.

**Additional optimization candidates:** Automatic framework introspection and generator execution remain LATER, outside Phase 3. A new global Gate or Role is REJECTED as redundant.

**Expected scope / risks:** Profile template and validator, Phase 3 verifier/report schema, optional Integration Gate hook, lifecycle/contract/Scenario evidence and matching documentation. False confidence from self-reported generation provenance is mitigated by reporting only hash integrity, not generator determinism or business correctness.
