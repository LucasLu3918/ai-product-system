# Scenario 072 — Gemini BeforeAgent Turn Context

Gemini CLI is integrated through the AIPS namespaced extension.

Expected:
- the extension defines a `BeforeAgent` hook;
- the hook injects compact current AIPS Turn Context before planning;
- the integration does not replace user-owned `GEMINI.md` or settings;
- verified installed state reports `TURN_NATIVE`;
- uninstall removes only the AIPS extension registration.
