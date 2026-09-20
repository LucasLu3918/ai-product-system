# Scenario 155 — Evolution Effectiveness Metrics and Feedback Loop

## Intent

Evolution Radar MUST measure which research sources and downstream decisions actually produce useful evidence without allowing metrics to automatically rewrite source policy or expand implementation authority.

## Expected behavior

- evaluate a bounded monthly cohort of durable weekly Evolution Radar Issues;
- read embedded weekly evidence, deterministic pre-analysis, semantic analysis, Human Decisions, Trial handoffs/results, and Trial→ADOPT bindings from durable Issue content/comments;
- bind the effectiveness report to the exact cohort issue manifest, repository revision, cohort month, and deterministic input digest;
- aggregate raw/unique signal observations and duplicate rate;
- aggregate deterministic shortlist and semantic-selection counts;
- aggregate latest semantic recommendation states and actionable ASSESS/TRIAL/ADOPT counts;
- aggregate Human Decision counts, provider-neutral `TRIAL_HANDOFF_READY` counts, Trial PASS/FAIL/BLOCKED counts, and adoption bindings;
- attribute collected/shortlisted/semantic/actionable/Trial/PASS/adoption observations back to exact source provenance;
- compute deterministic basis-point ratios for source shortlist yield, semantic yield, actionable conversion, Trial conversion, adoption conversion, and source failure rate;
- emit Human-review flags for sufficiently observed low-yield, high-failure, or zero-actionable sources;
- never automatically reweight, enable, disable, replace, or mutate a research source or source configuration;
- publish/update a durable monthly effectiveness Issue using `contents: read` + `issues: write` only;
- close a metrics Issue when no source review flag exists and leave/reopen it when deterministic Human-review flags exist;
- require no `OPENAI_API_KEY`, `GEMINI_API_KEY`, or other external Agent/provider credential;
- preserve Protected Human Authority for any source-policy change, implementation, PR, merge, release, or publication action beyond the metrics Issue itself.

## Rationale

v0.43–v0.45 make research broader, evidence stronger, and Trial execution provider-neutral. The next step is to measure research quality and conversion with durable evidence so future source-policy decisions are based on observed value rather than intuition. Metrics inform Human review; they do not self-optimize the system.
