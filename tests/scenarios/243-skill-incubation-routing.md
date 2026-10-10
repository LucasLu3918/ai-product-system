# Scenario 243 — LLM feature integration

## Request

> Add AI conversation summaries and ticket categories.

## Expected

- Define a schema, offline evaluation set and explicit thresholds; treat user/retrieved text as untrusted; restrict tools; describe failure behavior, privacy, cost and latency.
- Load only the relevant skill together with project-native instructions and any clearly applicable companion skill.
- State assumptions and unknowns; do not claim external or real-project validation that was not performed.

## Evidence

- The canonical skill frontmatter and method in skills/INDEX.yaml and the corresponding skills/**/SKILL.md.
- This scenario records expected routing and output behavior; it is manual semantic evidence, not an automated model-routing result.
