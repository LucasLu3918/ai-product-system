# Scenario 224 — Runtime-Preferred Primary Implementation Model

## Request

> Implement this bounded API change using the primary model I selected. Use helpers only if useful.

## Expected

- Preserve the eligible user/runtime primary model even when selected Skills prefer a lower tier.
- A legacy Execution Profile without optional routing-policy fields follows the same default.
- Use deterministic tools for repeatable discovery/checks and justify each delegated objective by evidence, risk, isolation or independent-review value.
- Auxiliary models resolve independently within host/user restrictions; unavailable selection is reported truthfully.
- Policy/privacy/tool/capability mismatches stop affected work and require an eligible route; primary preservation never overrides a critical floor.
- Required reviewer independence and risk floors remain intact, including targeted re-review.

## Must not

- Silently downshift the primary implementation model or hard-code a provider/model name.
- Treat an optional policy field as an actual host model switch.
- Replace required independent review with an author self-check.

## Evidence

Manual semantic acceptance scenario. Registry generation tests do not establish actual Agent routing behavior.
