# Scenario 177: Runtime Policy Enforcement

## Purpose

Verify deterministic action authorization, truthful native-hook enforcement, exact approval binding, and fail-closed high-risk egress.

## Given

- The policy defaults to `DENY` and the external destination is not allowlisted.
- SAL4 restricted financial data is sent toward an external processor.
- Runtime enforcement and sandbox network capabilities are independently verified.
- An Approval Record may or may not bind the exact action digest, destination, data labels, Change Boundary, policy digest, and expiry.

## Expected

- Unallowlisted destinations and secret exfiltration are `DENY` regardless of approval.
- SAL3/4 external actions require a matching allowlisted destination, verified `TOOL_GUARDED` hook, verified sandbox egress, and exact current human approval.
- Missing SAL/profile/sandbox proof is `BLOCKED`.
- A changed destination, arguments/profile digest, policy digest, data label, Change Boundary, or expired approval is `BLOCKED` as stale.
- Codex remains `ADVISORY`; a policy decision is not represented as mechanical enforcement there.
- Semantic `DENY`/`ESCALATE` may tighten an otherwise allowed result. Semantic `ALLOW`, timeout, or provider error cannot override deterministic `DENY` or produce an unverified `ALLOW`.
- A rule conditioned on exact destination host, port, method, and path allows only the full matching tuple; changing any one field denies. Unknown condition keys and invalid values fail policy validation.
- Missing, unreadable, malformed, or out-of-project Resource Authorization Profiles stay fail-closed and identify only a sanitized project-relative source, required resource/action, no-fallback status, and bounded recovery hint. Absolute paths and parser text never appear.
- A destination constraint denial reports only failed host/port/method/path fields with bounded actual and expected values; shared redaction removes credential-like query values.
- Claude `PreToolUse` exposes these details as bounded explanatory JSON while remaining a pre-execution denial. `PostToolUseFailure` remains a separate observation after start with only a parsed exit code when available; neither path retries or rolls back the action.
- Audit records contain action/policy digests and outcome metadata only; raw action arguments and secrets are absent.

## Limitations

Native pre-tool hooks can inspect only the payload delivered by their runtime. A direct `curl`/`wget` command can be classified conservatively; scripts, child processes, SDK calls, or hidden sockets require OS/sandbox network enforcement. `TOOL_GUARDED` does not mean network-isolated.
