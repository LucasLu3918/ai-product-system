# GitHub Repository Ruleset Policy Assessment

`config/github-ruleset-policy.yaml` describes the intended comparison. `scripts/github_ruleset_policy.py` consumes a complete, read-only snapshot; it does not query or mutate GitHub itself.

## Inputs

Dependency Review and scheduled Scorecard supplement security evidence; they do not change the configured required-check set or ruleset activation state.

The weekly Python compatibility smoke is supplementary evidence, not a required PR check. Branch protection continues to rely on the exact-candidate PR Gate and its Python 3.12 baseline.

The input must include branch protection, rulesets, bypass actors, and `source_complete: true`. Missing or permission-denied evidence yields `UNKNOWN`. The report exposes required checks added by the candidate. Preserve existing protection, the current required `repository` check, force-push/deletion restrictions, and known bypass actors; do not claim the policy is complete when bypass evidence is unavailable.

## Transition procedure

This assessment creates no ruleset and does not activate one. Before a future transition, retrieve the full current configuration again, inspect the exact policy diff and rollback path, verify account/API feature availability, and obtain approval for that exact candidate. Where GitHub's policy evaluation endpoint is unavailable to the account, keep evaluation as an operational review step and do not report an API evaluation result.
