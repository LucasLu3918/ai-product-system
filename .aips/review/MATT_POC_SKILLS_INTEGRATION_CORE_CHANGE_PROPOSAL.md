# Core Change Proposal — Matt Pocock Skills Routing and `grill-with-docs`

## Purpose

Preserve an independent, explicit-only `$grill-with-docs` entrypoint and make the pinned Matt Pocock Skills collection complete, inspectable, and routed according to overlap with existing AIPS capability.

## Why this is a core/large change

This changes Skill discovery and invocation semantics, expands the canonical Skill registry, adds a vendored external Skill source collection, and updates the generated Explorer, CLI inventory contracts, scenarios, and user guidance. Existing upstream classifications include deferred, reference-only, and unadopted entries that no longer match the approved routing direction for the seven pending in-progress/repo-tool Skills.

## Proposed Scope

### In scope

- Add AIPS canonical `grill-with-docs` as an independent explicit-only Skill. It uses AIPS requirement clarification one decision at a time, reads existing glossary/ADR conventions, and drafts documentation only after interview completion; writing project files requires separate user approval.
- Vendor all 38 source Skills from the pinned MIT commit `49dd158d1076134a641b33efb035946536778336` into a separate external source directory, outside the canonical AIPS Skill registry, and link each source manifest record to its vendored file.
- Reclassify the seven pending in-progress/repo-tool Skills under the agreed rule: overlap with AIPS becomes experimental/optional; a distinct capability becomes automatically routed on a matching request. Apply the same overlap rule to any other upstream entry previously marked not adopted, so duplicate setup/guardrail Skills remain discoverable as opt-in source.
- Bind each distinct automatic route to existing canonical Skill triggers and bounded project-safe procedures instead of treating an Explorer status label as runtime routing.
- Update the Explorer, `aips skills list --include-upstream`, Traditional Chinese descriptions, lifecycle/contract tests, Scenario 259, and Human guidance to explain source, routing, optional status, and explicit invocation.

### Out of scope

- Installing Skills into the user's global Codex/Claude/Gemini directories.
- Running upstream setup/migration instructions against user repositories or enabling background agents, schedules, or autonomous long-running goals.
- Changing Git authority, AIPS approval gates, or project-native ADR/Glossary conventions.

## Expected Files / Modules

- `skills/product/grill-with-docs/SKILL.md` and `agents/openai.yaml`; trigger/body extensions to the existing TDD and Technical Teaching Skills.
- `skills/INDEX.yaml`, `skills/locale/zh-TW.json`, and `skills/integrations/matt-pocock-skills.json`.
- `external-skills/matt-pocock/**`, with upstream MIT attribution retained.
- `scripts/skill_catalog.py`, generated `docs/human/public/skill-catalog.html`, and Skill CLI/projection lifecycle expectations.
- `tests/validation/skill_catalog_contracts.py`, relevant Skill lifecycle evidence, Scenario 259 and `tests/scenario_coverage.yaml`.
- `CHANGELOG.md`, `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`, documentation placement/sync registries, `docs/ARCHITECTURE.md`, and the Human/Agent Skill, Harness, Architecture, Technology, Conformance, Map and Maintenance guides.

## Impact

### Architecture / Contracts

Canonical Skills remain generated from `skills/**/SKILL.md`; vendored upstream source lives outside `skills/` and is not implicitly admitted to the canonical registry. The source manifest remains the single inventory and points to immutable, licensed vendored source. Distinct automatic routes resolve through canonical Skill triggers. Native explicit invocation metadata is carried with `grill-with-docs`.

### Data / Migration

No product data or persistent user configuration changes. Skill inventory grows by one canonical AIPS Skill and retains the 38 upstream entries.

### Security / Reliability

Upstream text is untrusted guidance. AIPS authority and project instructions take precedence. Upstream setup or filesystem instructions are never treated as permission; `grill-with-docs` only drafts ADR/Glossary changes and requires explicit approval before writing. No user-global skill install is performed.

### Compatibility / Rollback

Additive registry and documentation changes. Existing `aips skills list` default stays canonical-only; `--include-upstream` exposes the full source inventory and routing dispositions. Revert restores the previous inventory; no migration is needed.

### Tests / Validation

Impact-derived Test Matrix:

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Canonical Skill metadata and explicit-only native projection | Required | Skill index lifecycle | Native projection lifecycle | Registry uniqueness/frontmatter/explicit policy | N/A | Content/authority review | N/A | CLI list/install projection | Required | No runtime service changed |
| Vendored upstream inventory and routing | Required | Catalog contracts | Explorer generation | 38 unique source IDs/paths, pinned commit, license and status routing | N/A | Untrusted-source boundaries | N/A | `--include-upstream` CLI | Required | No user project mutation |
| Scenarios and Human documentation | Required | N/A | Scenario Conformance | Coverage and documentation placement | N/A | Secret scan | N/A | N/A | Required | Text behavior and metadata only |

Recompute trigger if scope expands: native runtime routing engine, new Capability/Role, global/user skill installation, arbitrary project writes, or changes to Git/approval authority.

Required release/CI evidence: repository preflight, Skill registry/catalog/CLI/projection lifecycle contracts, Scenario Conformance, documentation closure, secret scan, Core Change Test Matrix, exact-candidate Integration Gate, and required PR checks for the exact head.

### Secret / Credential Impact

Secrets required: NO

Approved acquisition mechanism: Not applicable.

Leakage/redaction review: Preserve upstream MIT license and source attribution; scan exact candidate.

Rotation/revocation plan if exposure is found: Not applicable; no secrets are introduced.

### Documentation / Diagrams

Architecture Diagram Impact:
- `docs/ARCHITECTURE.md`: add the registry and routing contract; Mermaid topology is unchanged because the existing Skill discovery/projection flow remains the same.
- `docs/human/ARCHITECTURE_OVERVIEW.md`: N/A — no runtime, capability, authority, or data-flow topology changes.
- Human SVG architecture/lifecycle diagrams: N/A — no component or lifecycle boundary is added.

## Risks

- A vendored upstream instruction may imply behavior outside AIPS authority; the catalog and source Skill must explicitly preserve AIPS precedence and user consent.
- Registry counts and native projection tests must be updated consistently when `grill-with-docs` becomes canonical.
- Partial repository Impact Graph coverage cannot establish all consumers; manually review catalog, CLI, generator, native projection, docs and scenario consumers.

## Recommendation

Proceed within the scope above. This follows the user's explicit direction to retain `$grill-with-docs`, include the seven pending source Skills, and make optionality depend on actual overlap.

## Proposed Implementation Order

1. Preserve the pre-change impact record and declare exact source, registry, projection, catalog, CLI, test, and documentation boundaries.
2. Add the explicit-only Skill, vendor pinned source, and update the manifest/routing UI.
3. Regenerate registry/Explorer and update tests/scenarios/docs.
4. Run targeted Skill lifecycle checks, repository preflight, Impact reconciliation, Core matrix, and exact-candidate Integration Gate.

## Approval

Status: APPROVED
Approved by: Human user
Approved at: 2026-10-12 (Asia/Taipei)
Approval record: Current instruction to retain `$grill-with-docs`, add the seven pending in-progress/repo-tool Skills, and classify only overlapping skills as experimental/optional; prior explicit approval to implement the recommended Skill integration.
Proposal fingerprint: sha256:6d0f496ba1a984e5b4d68ba75d901c146428dd02bd7fdcb2e8d8abe15b424e51
Scope fingerprint: sha256:ee417d3e8fca027416be25bc9b1879caac359e61e01145da263285480e01a070
Proposal fingerprint: sha256:7751433de147ade3f4870bbd3586018d7deccd4ba2d4f498d92e0d4a46b24523
Scope fingerprint: sha256:4c9a29ce9cf4a0c7d83705d50b2f5dd84da82f14c577679412c9c14629bba69f
Proposal fingerprint: sha256:7751433de147ade3f4870bbd3586018d7deccd4ba2d4f498d92e0d4a46b24523
Scope fingerprint: sha256:d6b139028477501f825045df50a81969d2d4a60029eaa0a26454fc8c00de57ab
