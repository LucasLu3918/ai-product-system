# GitHub Repository Ruleset Policy Assessment

`config/github-ruleset-policy.yaml` describes the intended comparison. `scripts/github_ruleset_policy.py` consumes a complete, read-only snapshot; it does not query or mutate GitHub itself.

## Inputs

Local Project Diagnostics does not inspect GitHub branch protection or ruleset snapshots. Remote policy remains UNKNOWN until a complete read-only repository snapshot is supplied to the canonical evaluator.

OpenCode integration candidates retain the Core classification and required repository checks. Native Host detection does not authorize remote publication or merge.

The read-only governance snapshot keeps its domain-independent digest facade over shared canonical JSON; unreadable GitHub policy surfaces remain `UNKNOWN` and do not gain authority.

The read-only snapshot command captures rulesets and branch protection independently; an inaccessible surface remains UNKNOWN and must not be treated as compliant.

Standalone and shadow dependency-review artifacts retain exact base/head, run ID, actual JSON findings and outcome for 90 days. Parity compares canonical findings; missing outputs, different candidates or inaccessible artifacts stay UNKNOWN. Job success alone cannot promote the shadow. Record resolved toolchain fingerprints and repeat full Gates only for new changes or unresolved failures.

The `repository` required context continues to cover full validation; the shared Python bootstrap is a caller-declared, fail-closed prerequisite within applicable workflows.

The existing `bin/aips` and `scripts/aips_cli.sh` entrypoints remain stable across internal CLI module extraction; this refactor does not alter GitHub ruleset inputs or remote protection authority.

Dependency Review and scheduled Scorecard supplement security evidence; they do not change the configured required-check set or ruleset activation state.

The weekly Python compatibility smoke is supplementary evidence, not a required PR check. Branch protection continues to rely on the exact-candidate PR Gate and its Python 3.12 baseline.

The input must include branch protection, rulesets, bypass actors, and `source_complete: true`. Missing or permission-denied evidence yields `UNKNOWN`. The report exposes required checks added by the candidate. Preserve existing protection, the current required `repository` check, force-push/deletion restrictions, and known bypass actors; do not claim the policy is complete when bypass evidence is unavailable.

## Transition procedure

Creative runtime reliability candidates preserve the Core change label and exact-candidate required checks. Synthetic engine success does not waive native callback/hook evidence or authorize modifying repository rulesets.

The local creative execution capability does not change protected-branch or merge policy; publish the exact reviewed candidate through the normal Integration Gate and Git Publish Approval flow.

Core Harness changes use the `aips:core-change` label on initial PR creation and require exact-candidate Integration Gate evidence; ruleset inspection remains read-only and separate from merge authority.

The creative Bundle change adds no ruleset or branch-protection mutation; the PR remains subject to the repository's existing Core checks and explicit publication/merge approvals.

The current policy path compares a complete read-only repository snapshot and reports `NO_CHANGE` or `NOT_READY`; it does not activate rulesets or alter branch protection. Any future transition requires a fresh settings snapshot, recovery plan and explicit approval.

This assessment creates no ruleset and does not activate one. Before a future transition, retrieve the full current configuration again, inspect the exact policy diff and rollback path, verify account/API feature availability, and obtain approval for that exact candidate. Where GitHub's policy evaluation endpoint is unavailable to the account, keep evaluation as an operational review step and do not report an API evaluation result.

- GitHub ruleset assessment and release readiness remain separate read-only decisions; a ready result still cannot write a version tag.
