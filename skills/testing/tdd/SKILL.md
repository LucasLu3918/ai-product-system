---
id: tdd
description: Implement testable behavior through failing tests, minimal passing changes and refactoring; use characterization tests for legacy behavior and configure requested test tooling.
capability: testing
estimated_context_cost: low
triggers:
- testable_behavior_change
- modifying_testable_behavior
- implementing_business_rules
- implementing_api_or_service_behavior
- typescript_test_fixture_migration
- pre_commit_validation_setup
- commit_hook_configuration
model_requirements:
  reasoning: medium
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Test-Driven Development

Default cycle for testable behavior:

1. RED — express the required behavior with a failing test.
2. GREEN — implement the smallest change that passes.
3. REFACTOR — improve structure while tests remain green.

For legacy code with insufficient coverage, create characterization tests around behavior that must remain stable before risky modification.

Do not force unit-test-shaped TDD onto purely visual work, generated code or configuration where another validation strategy is more appropriate.
## Test design quality

At each red-green-refactor cycle, test through the smallest public behavior seam that can observe the requirement. Prefer assertions whose expected values come from an independent example or accepted specification. Avoid tests coupled to private implementation, tautological expectations, and batches of tests written before the first vertical slice. Agree on a test seam with the user only when the seam itself is a material product or contract decision; routine test boundaries are an implementation choice.

## Test fixtures and repository tooling

- For a requested TypeScript test-fixture migration to `@total-typescript/shoehorn`, inspect the package manager, TypeScript version and existing fixture conventions first. Prefer narrowly replacing unsafe assertions where a partial fixture improves the test; do not run a blanket rewrite or add a dependency unless the task authorizes it.
- For requested pre-commit or commit-hook setup, preserve existing hooks and package-manager conventions. Reuse existing lint, type-check and test scripts; add only the smallest configured checks the user requested. Validate configured tool versions and avoid introducing a second hook manager.
- Configuration changes follow the target project's Change Impact and validation requirements; this Skill does not authorize installing dependencies or overwriting existing setup by itself.

Source note: adapted from mattpocock/skills engineering/tdd at 49dd158d1076134a641b33efb035946536778336 (MIT); see licenses/MIT-Matt-Pocock-Skills.txt.
