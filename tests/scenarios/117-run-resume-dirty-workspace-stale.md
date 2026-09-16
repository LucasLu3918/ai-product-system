# Scenario 117 — Resume Detects Dirty Workspace Drift

A run checkpoint is created and Git HEAD remains unchanged.

Then a tracked product file is modified without committing.

Expected:
- resume becomes STALE;
- the reason includes dirty workspace drift;
- restoring the exact workspace returns resume to CURRENT;
- AIPS-owned `.ai/` checkpoint writes do not stale the product workspace fingerprint.
