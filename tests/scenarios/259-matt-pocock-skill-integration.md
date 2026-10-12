# Scenario 259 — Matt Pocock Skill Integration and Explorer

## Setup

- The AIPS Skill registry includes five approved distinct additions, three optional Writing workflow Skills, and the explicit-only `grill-with-docs` entrypoint.
- All 38 Skills from commit `49dd158d1076134a641b33efb035946536778336` are vendored under `external-skills/matt-pocock/` with source digests and MIT attribution.
- The seven pending in-progress/repo-tool Skills are classified by overlap: four are experimental/optional and three distinct workflows auto-route when their task matches.
- The Skill Explorer is generated from the canonical registry and source disposition manifest.

## Exercise

1. Search and filter active AIPS Skills by name, purpose, category and state; copy a prompt example.
2. Inspect an upstream record and confirm its disposition and AIPS mapping are visible.
3. Request ordinary writing help and confirm the Writing Fragments → Beats → Shape workflow is not implied.
4. Explicitly request that workflow and confirm its three Skills are available as opt-in methods.
5. Inspect all seven pending in-progress/repo-tool entries and confirm overlapping entries are experimental/optional while distinct tools auto-route only on matching requests; verify `aips skills list --trigger` resolves shoehorn migration, exercise scaffolding and pre-commit setup to their canonical Skills.
6. Confirm the vendored source path and digest for each upstream record and review the pinned commit and MIT license.
7. Run `aips skills list` and confirm it shows the 49 AIPS Skills in Traditional Chinese; add `--include-upstream` and confirm all 38 source records include routing status, AIPS mapping and local source path.
8. Invoke `/grill-me` explicitly and confirm it asks one decision-focused question at a time; confirm ordinary requests do not start that interview.
9. Invoke `$grill-with-docs` and confirm it remains an independent explicit-only Skill, prepares glossary/ADR drafts from settled decisions, and respects project write approval.
10. Run `aips skills install --upstream --all` in an isolated home and confirm only the six unique optional source Skills are installed; four same-ID source entries resolve to canonical AIPS Skills, other dispositions are reported as skipped, repeat installation is idempotent, and status can filter upstream ownership.
11. Remove one upstream Skill and then all upstream Skills for selected Hosts; confirm AIPS catalog and Portable Command Skills remain, shared Codex/Gemini projections remain until their final Host reference is removed, and modified source files plus user resources are preserved.
12. Install one upstream Skill into Claude workspace scope and confirm status and uninstall are restricted to that project; confirm scripts and hooks are not executed or configured by installation.

## Expected result

- All 49 registered AIPS Skills and all 38 vendored upstream records are discoverable in the Explorer and CLI.
- CLI JSON output preserves source, status and AIPS target fields; the default list remains limited to active AIPS Skills.
- `/grill-me` reuses the requirement clarification workflow and requires explicit invocation.
- New distinct Skills reuse existing AIPS authority and do not add Roles or Capabilities.
- Optional Writing Skills require explicit user direction; overlapping source skills remain experimental/optional.
- Distinct repo/tool source skills are automatically routed only for their matching task.
- `grill-with-docs` is available as `$grill-with-docs` but is not implicitly invoked.
- Human-guided steps do not collect or expose secrets; no upstream installation hooks are introduced.
- Upstream native install selects only optional dispositions, rejects unsafe source paths/digests, skips canonical duplicate IDs and uses the existing per-file ownership manifest for safe status/uninstall.
- `--upstream` install/uninstall never modifies AIPS catalog or Portable Command ownership; modified Skills and user-added resources remain available after removal.
- The Explorer distinguishes active Skills from deferred, excluded, reference-only and unadopted source items.

## Coverage

`tests/evidence/skills_cli_lifecycle.py` deterministically verifies the native install/status/uninstall lifecycle in isolated Host directories. Manual semantic acceptance remains required for natural-language routing; `tests/validation/skill_catalog_contracts.py` checks inventory completeness, explicit Writing triggers, Beta exclusion, generated output and registry wiring.
