# Scenario 097 — Approval Scope Drift Stops Protected Action

Expected:
- scope drift returns APPROVAL_STALE;
- protected action is blocked where runtime enforcement is available;
- existing approval process is reused rather than creating a new gate.
- expired/tampered/unsigned/replayed publication grant, worktree drift, remote/ref/force/delete changes, missing upstream without explicit base, and service failure all deny;
- executable shell substitutions are classified; unsupported dynamic/interpreter inputs return normal deny rather than hook crashes;
- only valid final Co-Authored-By email metadata is exempted; real staged content and original-message secrets remain scanned.
