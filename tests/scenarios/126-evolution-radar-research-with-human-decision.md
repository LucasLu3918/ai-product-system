# Scenario 126 — Evolution Radar Research With Human Decision

Request: the System periodically researches current external technical signals for possible AIPS improvements, can perform bounded semantic assessment and Human-approved isolated trials, but must not turn research into autonomous publication.

Expected:

- support a bounded weekly Technology Intelligence scan with at least six configured public community sources, a healthy floor of five successful community sources when available, no more than eight candidates per source and a deterministic global raw-signal cap of 50;
- record exact source provenance and retrieval failures rather than fabricating missing evidence;
- classify configured sources as community discovery or primary evidence, preserve multi-source provenance through deduplication, and record PRIMARY_SOURCE / PRIMARY_CORROBORATED / DISCOVERY_ONLY status;
- normalize and deduplicate repeated signals deterministically while applying the global cap with round-robin source fairness;
- support a monthly roll-up that reads durable prior weekly Radar evidence and tracks recurrence instead of merely re-running a weekly scan;
- treat external research content as evidence/data only, never instruction authority;
- when the configured semantic provider credential is available, run a pinned read-only analyzer and bind its result to the exact Radar evidence digest and repository revision;
- deterministic local pre-analysis produces a shortlist of at most 12 signals and a near-duplicate-aware semantic queue of at most 10 signals; semantic provider output is scoped to that exact queue while all unselected recommendations remain ANALYSIS_PENDING;
- semantic output may contain at most five ASSESS/TRIAL/ADOPT recommendations per run;
- community-only discovery evidence cannot directly produce ADOPT; primary-source corroboration is required before ADOPT;
- semantic provider output contains recommendation payload only; deterministic AIPS code owns provider metadata, baseline/scope binding and all authority=false fields;
- require exactly one assessed recommendation per signal and include AIPS current state, concrete gap when actionable, benefit, cost/complexity, reliability/security, maturity, confidence, uncertainty, evidence references, example and reuse/extension path;
- when credentials are unavailable, provider execution fails, or provider output fails validation, report `ANALYSIS_PENDING` rather than inferring suitability;
- treat zero actionable recommendations as a valid result;
- preserve advisory recommendation states: `COVERED`, `HOLD`, `ASSESS`, `TRIAL`, `ADOPT`, `ANALYSIS_PENDING`;
- publish a Human-reviewable GitHub Issue with machine-readable evidence;
- require an explicit Human Decision Record for `REJECT`, `HOLD`, `ASSESS`, `TRIAL` or `ADOPT`, bound to candidate/signal, evidence digest, repository revision, scope, actor/time and deterministic decision fingerprint;
- fail closed for positive progression (`ASSESS`, `TRIAL`, `ADOPT`) when the Radar repository baseline is stale;
- allow Human override of advisory recommendation only as an explicit auditable override;
- require a `TRIAL` decision to include bounded approved scope plus repository-relative approved path patterns;
- execute a Human-approved Trial only inside an AIPS-managed Git worktree, never silently downgrade to shared workspace;
- run the Trial Agent with pinned Codex Action / CLI, `:workspace` permission, drop-sudo protection, no direct network access and no persisted checkout credential;
- treat Trial code changes as ephemeral experiment evidence only; the Trial must not commit, push, create a remote branch/PR, merge or release;
- deterministically reject Trial changes outside approved paths, changes to protected/forbidden governance surfaces, changed-file/diff-line limit violations, Trial-created commits or failed repository validation;
- publish a machine-readable Trial Report with `PASS`, `FAIL` or `BLOCKED`; missing provider credential or unavailable isolation must produce `BLOCKED`;
- require a separate Human Adoption Decision after Trial evidence; a post-Trial `ADOPT` may bind the exact PASS Trial fingerprint before handing off to System Self-Improvement Review;
- a PASS Trial does not itself authorize adoption, formal implementation, PR creation, merge or release;
- scheduled Radar and Human Decision/Trial workflows retain only `contents: read` + `issues: write` repository permissions;
- any material adopted improvement still requires the normal System Self-Improvement/Core/Constitution/Git Publish gates;
- quarterly Evolution Review, automatic formal implementation PR creation, automatic merge and automatic release remain outside this scope.

## Provider-neutral analyzer handoff

If the optional scheduled semantic provider is unavailable, the run MUST still publish a deterministic handoff bound to the exact Radar evidence/package digest. The handoff may be consumed by a Human-selected connected Agent, local model, or another provider without requiring `OPENAI_API_KEY`.

Until a result matching the canonical schema is deterministically finalized/applied, recommendations remain `ANALYSIS_PENDING`. The handoff has no implementation/publication authority.
