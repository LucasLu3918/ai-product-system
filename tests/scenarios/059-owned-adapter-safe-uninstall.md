# Scenario 059 — AIPS-owned Adapter Safe Uninstall

AIPS created a Codex global bootstrap because no user file existed.

Expected:
- ownership snapshot/manifest is recorded;
- if the live file still matches the AIPS-owned copy, uninstall removes it;
- user/project Skills and source are unaffected.
