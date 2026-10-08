# System Improvement Review: Creative Bundle Preparation and MFLUX Mapping

## Problem and recommendation

- **Appropriateness:** Appropriate. Existing character profiles, style profiles, artwork manifests, composition and human review already cover consistency and presentation. The remaining gaps are a safe starter workflow and fixed CLI compatibility for the already-supported MFLUX provider.
- **User problem:** Starting a local character workflow requires copying and filling several files by hand; model-family executable and edit argument differences are not represented by one deterministic capability map.
- **Proposed solution:** Add a bounded `prepare` action and explicit MFLUX model/operation command mappings, preserving local-only execution and the existing quality review workflow.
- **Existing coverage:** `scripts/creative_workspace_profile.py`, `templates/creative/CHARACTER_PROFILE.yaml`, `STYLE_PROFILE.yaml`, `CREATIVE_BUNDLE.yaml`, `scripts/creative_execution.py`, and Scenario 234/236 already provide the closest reusable behaviors.
- **Reuse / extension candidates:** Extend the existing Creative Bundle executor, template set and OpenCode `creative_execution` tool. Do not introduce a new Role, Skill, Capability or approval gate.
- **Lower-layer alternative:** Keep the starter files in the existing user-selected EPHEMERAL workspace. Do not add a global project initializer or automatic model provisioning.
- **Context / token cost:** No bootstrap additions. The command and model map load only on a relevant creative task; generated files are a fixed bounded set.
- **Security / reliability:** Preparation is non-Git only, project-relative, symlink/traversal guarded, create-only, versioned and serialized across concurrent callers. MFLUX calls use fixed argv and offline flags. ComfyUI retains loopback/built-in-node constraints and exactly one hash-checked edit reference. No downloads or external image egress.
- **Backward compatibility:** Additive CLI action and optional `input_images`; existing `input_image`, `dev` and `schnell` bundles retain their behavior. No persisted schema migration.
- **Scenario / test impact:** Extend Scenario 236 with concurrent preparation, collision/path rejection, fixed MFLUX command mapping and batch limits; use fake local providers only.
- **Human docs impact:** Update User Guide, Technology Guide, Maintenance, Architecture Overview and Scenario Conformance.
- **Agent docs impact:** Update Creative Direction and OpenCode compatibility/Conformance guidance.
- **Architecture diagram impact:** Update `docs/ARCHITECTURE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md` and `docs/human/assets/harness-overview.svg`. System overview remains N/A because it depicts the broad access plane, not this bounded tool workflow. Project Intelligence and system lifecycle diagrams remain N/A because identity, persistence and installation lifecycles do not change.
- **Constitution impact:** NO. No change to human authority, safety boundary, precedence or approval semantics.
- **Recommended AIPS solution:** Extend the existing local creative workflow and templates with a safe preparation action and fixed MFLUX capability registry; require explicit preflight/execute and independent human visual review.
- **Additional optimization candidates:** None added to this scope. Model downloads/training remain explicitly excluded.
- **Expected scope:** `scripts/creative_execution.py`, CLI and OpenCode routing, Bundle template, Scenario 236, associated evidence, canonical docs/diagrams, documentation maps, version and changelog.
- **Risks:** Host-installed MFLUX variants may expose different CLI flags; unsupported combinations must remain blocked until verified against upstream command documentation.

## Approval record

The user explicitly approved the full scope on 2026-10-08: “核准上述完整範圍”. This is the required Core Change Approval. Publication approval remains bound to the exact final candidate and is handled separately.
