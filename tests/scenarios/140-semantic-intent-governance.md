# Scenario 140 — Provider-Neutral Semantic Intent Governance

## Given
Resource Authorization has evaluated a declared resource operation and a provider-neutral semantic assessment is bound to the exact intent request fingerprint.

## When
AIPS evaluates the finalized intent evidence.

## Then
Intent evidence may only narrow permission: an authorization DENY can never become compatible, and an existing ALLOW is compatible only when the bound intent state is ALIGNED. AMBIGUOUS, MISALIGNED or HIGH_RISK evidence blocks compatibility. No provider is required by AIPS core, private reasoning and secrets are rejected, and the evidence grants no tool-call, Human, merge, release or protected-operation authority.
