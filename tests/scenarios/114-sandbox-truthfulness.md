# Scenario 114 — Sandbox capability is truthful

## Given
No enabled sandbox provider has a fresh verification record bound to the current capability registry.

## When
Sandbox isolation is resolved or creation is requested.

## Then
- no enabled provider reports UNSUPPORTED;
- an enabled but unverified, stale or control-incomplete provider reports BLOCKED;
- a verified provider is eligible only when its runtime class and data policy meet the request;
- AIPS does not create a temporary directory presented as a sandbox.
