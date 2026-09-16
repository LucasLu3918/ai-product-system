# Scenario 103 — Resume Detects Revision Drift

Expected:
- a changed Git HEAD after checkpoint returns STALE;
- requires_freshness_check is true;
- the Agent refreshes/revalidates affected evidence before continuing;
- stale evidence is never silently accepted.
