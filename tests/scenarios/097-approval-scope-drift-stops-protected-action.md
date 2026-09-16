# Scenario 097 — Approval Scope Drift Stops Protected Action

Expected:
- scope drift returns APPROVAL_STALE;
- protected action is blocked where runtime enforcement is available;
- existing approval process is reused rather than creating a new gate.
