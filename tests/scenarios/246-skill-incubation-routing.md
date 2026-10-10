# Scenario 246 — database migration

## Request

> Split a populated users.name column into first and last names.

## Expected

- Plan expand/migrate/contract; assess locks and backfill batches; preserve old/new version compatibility; define consistency checks and recovery; gate irreversible deletion for human approval.
- Load only the relevant skill together with project-native instructions and any clearly applicable companion skill.
- State assumptions and unknowns; do not claim external or real-project validation that was not performed.

## Evidence

- The canonical skill frontmatter and method in skills/INDEX.yaml and the corresponding skills/**/SKILL.md.
- This scenario records expected routing and output behavior; it is manual semantic evidence, not an automated model-routing result.
