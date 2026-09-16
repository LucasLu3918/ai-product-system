# Scenario 059 — AIPS-owned Adapter Safe Uninstall

AIPS composed a managed runtime instruction block and recorded ownership.

Expected:
- ownership snapshot/manifest is recorded;
- if the live managed block still matches the AIPS-owned snapshot, uninstall removes only that block;
- pre-existing user content in the same file remains unchanged;
- user/project Skills, source and unrelated runtime settings are unaffected.
