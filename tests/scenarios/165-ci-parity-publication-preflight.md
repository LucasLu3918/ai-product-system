# Scenario 165 — CI-Parity Publication Preflight

## Given

A publication candidate may include committed, staged, unstaged and untracked paths, and may affect documentation placement, change classification, Core Change matrix requirements, protected-branch routing, runtime validation capabilities and post-squash local state.

## When

The maintainer previews a working tree, binds the reviewed Core Matrix, then runs the shared publication preflight locally while GitHub validates the pull request and any classification-label changes.

## Then

- local and CI resolve the same exact base/head, change class and canonical matrix contract;
- preview includes untracked and uncommitted paths and explains why every documentation path is required;
- Core Matrix binding refresh updates base/hash and invalidates prior READY/reconciled state for review;
- the Gate fails if a test command reports fewer or more than its declared expected test count;
- adding or removing a change-class label triggers a fresh validation run;
- diff-aware documentation impact runs before expensive lifecycle validation;
- missing base or required documentation cannot be reported as CI-parity PASS;
- Git-ignored local metadata does not violate documentation audience layout;
- unsupported localhost/browser capabilities are reported as environment blockers;
- explicit `--project-root` keeps source scripts, configuration, candidate identity and the Integration Gate on one checkout;
- changed Markdown local links and the local VitePress build fail before the full publication Gate;
- missing Python, Ruff, loopback or browser prerequisites return remediation before candidate scanning and lifecycle execution;
- the Integration Gate selects an explicitly configured or complete prepared Python 3.12 venv; it rejects incomplete dependencies, including a missing OpenAPI validator, before candidate checks start;
- local docs preflight uses Node 24+ from `PATH` or `AIPS_NODE_BINARY` and invokes the installed VitePress bundle directly; it does not install packages or contact a registry;
- missing Change Impact final dispositions show allowed choices while unknown and high-risk findings remain blocking;
- the Core/Large classification label is present in the initial PR creation request, and missing GitHub CLI authentication is reported without raw stderr;
- protected main routes through a pull request;
- post-merge reconciliation requires a clean tree, preserves a backup branch and fast-forwards only when local main is an ancestor of the fetched target; divergent histories block, while equivalent trees retain the existing guarded reconciliation;
- validation runs share a PR-number concurrency group; a newer candidate or Core/Large classification-label event can supersede stale validation, while unrelated label events neither cancel active runs nor execute the expensive Gate;
- a skipped Janitor satisfies the existing `repository` required aggregate only for an unrelated `labeled`/`unlabeled` event, with an explicit Step Summary; a failed or skipped classification-label Gate remains blocking;
- a clean local main fast-forwards only when it is an ancestor of the fetched target, preserves its old tip as a backup, and leaves divergent histories untouched;
- Project Intelligence revision refresh occurs automatically only for equivalent trees; semantic changes remain fail-closed;
- publication, reset and merge authority remain Human-controlled.

Recovery regression: implicit checkout routing and explicit project-root select the intended script; configured Python serves Intelligence; document prechecks publish bounded missing paths; CI summaries show Gate durations and the slowest ten checks. Offline wheelhouse installs avoid package-index requests. Repeated Intelligence bootstrap preserves state, and refresh-plan never approves stale sources.
