# Scenario 244 — E2E browser testing

## Request

> Verify sign-up, email verification, login and first-project creation.

## Expected

- Route critical journeys to browser E2E; isolate test data and mock email; prefer role/label selectors; capture trace/screenshot evidence on failure; use test-only credentials.
- Load only the relevant skill together with project-native instructions and any clearly applicable companion skill.
- State assumptions and unknowns; do not claim external or real-project validation that was not performed.

## Evidence

- The canonical skill frontmatter and method in skills/INDEX.yaml and the corresponding skills/**/SKILL.md.
- This scenario records expected routing and output behavior; it is manual semantic evidence, not an automated model-routing result.
