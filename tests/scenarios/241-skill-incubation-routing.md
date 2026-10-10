# Scenario 241 — systematic debugging

## Request

> An intermittent stack trace.

## Expected

- Route code-level failures to this skill; reproduce and isolate before editing; verify a specific root-cause hypothesis; add a regression test and report evidence; do not route an active outage or performance-only regression here.
- Load only the relevant skill together with project-native instructions and any clearly applicable companion skill.
- State assumptions and unknowns; do not claim external or real-project validation that was not performed.

## Evidence

- The canonical skill frontmatter and method in skills/INDEX.yaml and the corresponding skills/**/SKILL.md.
- This scenario records expected routing and output behavior; it is manual semantic evidence, not an automated model-routing result.
