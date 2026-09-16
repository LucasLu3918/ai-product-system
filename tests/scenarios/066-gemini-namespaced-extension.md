# Scenario 066 — Gemini Namespaced Extension

Gemini CLI is available and no aips-global-harness extension collision exists.

Expected:
- AIPS uses the official extension mechanism with an AIPS namespace;
- user GEMINI.md/settings are not overwritten;
- adapter is recorded as AIPS-owned;
- uninstall unregisters only aips-global-harness.
