# Scenario 097 — Approval Scope Drift Stops Protected Action

Expected:
- scope drift returns APPROVAL_STALE;
- protected action is blocked where runtime enforcement is available;
- existing approval process is reused rather than creating a new gate.
- expired/tampered/unsigned/replayed publication grant, worktree drift, remote/ref/force/delete changes, missing upstream without explicit base, and service failure all deny;
- executable shell substitutions are classified; unsupported dynamic/interpreter inputs return normal deny rather than hook crashes;
- only valid final Co-Authored-By email metadata is exempted; real staged content and original-message secrets remain scanned.
- personal mode is selected only when the fixed administrator trust-root file is absent; a present invalid/unreadable root fails closed without downgrade.
- personal mode permits only the current `agent/`, `bugfix/`, `chore/`, `claude/`, `codex/`, `docs/`, `feature/`, `fix/`, `gemini/` or `work/` branch to push to its same-named remote engineering branch; direct protected/default branch push, deletion, tags and releases remain denied.
- PR create/merge retain exact candidate/ref validation; merge into `main` additionally requires task authorization and passing required checks.
