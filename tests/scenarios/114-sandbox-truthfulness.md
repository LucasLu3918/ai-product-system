# Scenario 114 — Sandbox capability is truthful

## Given
No verified sandbox provider is registered.

## When
Sandbox isolation is resolved or creation is requested.

## Then
AIPS reports UNSUPPORTED/BLOCKED and does not create a temporary directory presented as a sandbox.
