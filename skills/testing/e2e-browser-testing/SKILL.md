---
id: e2e-browser-testing
description: Verify critical user journeys in a real browser with deterministic setup,
  stable selectors and useful failure artifacts.
capability: testing
estimated_context_cost: low
triggers:
- critical_user_flow
- e2e_test_request
- flaky_ui_test
model_requirements:
  reasoning: medium
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# E2E Browser Testing

Use the browser automation framework already adopted by the project; use Playwright when no framework is established and the project supports it. Use tdd for a single function or module and security-testing when the objective is a security property.

## Method

1. Select a user journey with meaningful business or user impact and define its observable success and failure outcomes.
2. Control environment, clock, network, and test data. Isolate accounts and clean up created state. Use test credentials only.
3. Prefer accessible role/name and label selectors; use stable test IDs where semantics are insufficient. Avoid brittle CSS paths and fixed sleeps.
4. Assert user-visible outcomes and important state transitions, not implementation details. Cover relevant empty, validation, authorization, error, and recovery paths.
5. Make retries diagnostic, never a substitute for stability. On failure retain the browser trace, console/network evidence, and a screenshot when the runner supports them.
6. Run locally and in CI using the same setup contract; document required services and test data.

## Output

Record the journey, setup and cleanup, assertions, commands, and failure artifacts. Do not use production accounts, live customer data, or real external side effects.
