# Scenario 259 — Matt Pocock Skill Integration and Explorer

## Setup

- The AIPS Skill registry includes five approved distinct additions and three optional Writing workflow Skills.
- The pinned upstream inventory classifies all 38 Skills from commit `49dd158d1076134a641b33efb035946536778336`.
- The Skill Explorer is generated from the canonical registry and source disposition manifest.

## Exercise

1. Search and filter active AIPS Skills by name, purpose, category and state; copy a prompt example.
2. Inspect an upstream record and confirm its disposition and AIPS mapping are visible.
3. Request ordinary writing help and confirm the Writing Fragments → Beats → Shape workflow is not implied.
4. Explicitly request that workflow and confirm its three Skills are available as opt-in methods.
5. Inspect untested upstream Beta entries and confirm they remain excluded from AIPS routing.
6. Review source attribution, pinned commit and MIT license.

## Expected result

- All 48 registered AIPS Skills and all 38 upstream dispositions are discoverable in the Explorer.
- New distinct Skills reuse existing AIPS authority and do not add Roles or Capabilities.
- Optional Writing Skills require explicit user direction.
- Human-guided steps do not collect or expose secrets; no upstream installation hooks are introduced.
- The Explorer distinguishes active Skills from deferred, excluded, reference-only and unadopted source items.

## Coverage

Manual semantic acceptance. `tests/validation/skill_catalog_contracts.py` deterministically checks inventory completeness, explicit Writing triggers, Beta exclusion, generated output and registry wiring; it does not prove model routing quality for every natural-language request.
