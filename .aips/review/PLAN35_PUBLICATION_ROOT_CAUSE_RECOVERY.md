# Plan35 — Publication Root-Cause Recovery

Request: the Human asked AIPS to implement the previously reviewed diagnostics and safe recovery plan.
State: CHANGES PROPOSED FOR PR REVIEW. This document is not a native Claude Host permission, a signed grant, or proof of AIPS publication approval.
Baseline: v0.82.0, main b615db299c9c8329d8fa218d8dd8cd81eb82042c.

## Scope

- Reuse existing publication authority/diagnostics/planning, not a second gate.
- Distinguish exact merge-command failures from generic publication rejection.
- Do not report absent Required Checks as pending without independently verified policy evidence.
- Add sanitized Host-denial classification and advisory read-only recovery guidance.
- Update Claude Code harness guidance, traditional-Chinese Human docs, Scenario 260 and regression tests.

## Boundaries

No branch protection or ruleset changes, no permission bypass, no token acquisition, no automatic merge, no branch cleanup, no release/tag, no storage schema changes. Personal versus High-Assurance Human authority remains unchanged. Unknown CI/policy evidence fails closed. Do not treat PR creation through an external connector as native AIPS Hook or Integration Gate evidence.

## Verification and acceptance

Focused unit/contract tests, lifecycle tests, documentation placement impact, full repository validator, exact-candidate integration gate, independent security review and PR checks. Reconcile known Python matrix failures already present on base SHA separately. A real installed Claude Code interactive test remains necessary for Host classifications. Revert this PR to roll back; no remote admin settings change.
