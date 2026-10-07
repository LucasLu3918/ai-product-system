# Scenario 225 — Skill Metadata Single Source

## Request

> Change a Skill trigger and regenerate the routing registry without changing consumer contracts.

## Expected

- SKILL.md frontmatter is canonical for id, capability, triggers, context cost and model requirements.
- Deterministic generation preserves the version 1 INDEX shape and tier fields.
- Default check is read-only; drift fails until explicit regeneration.
- Reject duplicate IDs/keys, applies_when duplicates, missing/invalid requirements, invalid tiers and symlink escapes.
- Repeated generation produces identical bytes; existing MCP/catalog consumers can still resolve every path.

## Evidence

`tests/evidence/skill_index_lifecycle.py` verifies generation, drift, malformed metadata, containment and v1 compatibility. It does not claim semantic model-routing quality.
