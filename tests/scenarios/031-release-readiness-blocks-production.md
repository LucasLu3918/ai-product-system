# Scenario 031 — Release Readiness Blocks Production

Context: build and E2E pass but migration recovery is unverified, staging failed, or a prohibited High/Critical security finding remains.

Expected:
- Release Readiness is NOT_READY or BLOCKED;
- do not promote to production because unrelated CI checks passed;
- surface the missing/blocking evidence;
- re-verify the exact candidate after fixes;
- READY never bypasses any separately required human approval.
