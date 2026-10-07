# Plan19 — Architecture Truth & Runtime Closure

## Approved scope

User approved all nine Plan19 recommendations. Implement them in bounded stages in one candidate branch, preserving current public formats and Human Authority.

1. Add one canonical Capability Registry and deterministic generation for the existing Capability Map and architecture-surface inventory. Repository Health must detect unmapped major surfaces.
2. Prototype Codex PreToolUse denial against one harmless synthetic command. Record supported/unsupported paths and timeout/error behavior. Keep the adapter ADVISORY unless evidence supports a narrower, truthful capability claim.
3. Extend Quality Ratchet with measured per-module budgets and report-only coverage baselines. Do not tighten required thresholds in this change.
4. Extract one cohesive internal storage boundary from project_intelligence.py only if dependency and lifecycle inspection confirm facade, symbol-identity, CLI, and persistence compatibility.
5. Add a behavior-to-Scenario/Eval dependency map and a deterministic freshness report that selects only affected Agent Eval cases. Keep Scenarios 192, 193, and 224 manual until real provider-neutral behavioral evidence exists.
6. Complete Release Channel readiness and version/tag/installer consistency checks. Do not create a Git tag or GitHub Release.
7. Add provider-neutral advisory usage/cost budget fields and telemetry projection. Report observed usage only when a runtime supplies it; leave price and cost unknown without a verified price source. Do not add an LLM Gateway.
8. Reconcile current branch metadata into a draft exact-SHA cleanup proposal for human review. Do not delete remote branches.
9. Use existing Evolution Radar exclusion attribution/effectiveness evidence to produce a fresh report. Keep scoring unchanged until enough new evidence supports a reviewed adjustment.

## Evidence and fit

The repository already has the relevant subsystems. This change joins their sources and adds missing evidence without adding a Role, Skill, generic approval Gate, or central provider dependency. Baseline evidence is in PLAN19_BASELINE.yaml. The September Radar cohort is 100 raw/unique signals and zero shortlist; exclusion attribution is newly available, so immediate ranking changes would be premature.

Official Codex hooks can deny supported PreToolUse calls. Timeout, callback error, malformed output, and some specialized tool paths may fail open or bypass the hook. The probe therefore cannot upgrade Codex as a whole to TOOL_GUARDED.

## Compatibility, security, and authority

- Existing map and surface outputs remain compatible; generated ownership is explicit.
- Persisted fields are additive. Existing consumers must continue to read old data.
- Quality defaults remain non-blocking until a measured graduation is separately justified.
- The Codex probe runs only against a harmless synthetic command in an isolated fixture; it does not change user-global hook trust or settings.
- Branch cleanup and Release creation remain separate Human-approved actions.
- No Constitution semantics change. Human decisions, merge authority, and release authority remain unchanged.
- No sensitive user data, provider credential, prompt, or private reasoning is added to telemetry.

## Risks and mitigations

- A dual-source registry migration could drift: deterministic generation, check mode, and lifecycle tests must detect stale outputs.
- Hook demonstrations could overstate enforcement: report capability per event/tool path and retain ADVISORY on any gap or fail-open behavior.
- A broad core module extraction could break CLI/import identity: perform at most one extraction and keep it only if lifecycle evidence passes.
- New cost fields could imply false precision: omit unavailable usage and represent estimate confidence/price availability explicitly.
- Remote branch metadata can change after capture: bind every draft entry to an exact SHA and require refresh/revalidation before any later approved deletion.

## Change boundaries

Target subsystems: capability inventory/Repository Health; Codex adapter hook prototype; Quality Ratchet; one Project Intelligence storage seam; Agent Eval freshness; Release Channel readiness; Execution Profile/Telemetry; Branch Hygiene proposal evidence; Evolution Radar effectiveness report.

Documentation and affected architecture diagrams must follow the repository Documentation Impact Gate. The Constitution, central LLM routing/Gateway, broad coverage percentage, automatic branch deletion, and actual Release/tag creation are out of scope.

## Validation

Use the exact-candidate Core Change Test Matrix. Run the repository validator, focused contracts/lifecycles for each changed boundary, module-facade checks, Scenario Conformance, documentation placement/build, Release/Branch dry runs, telemetry privacy/unknown-value cases, strict secret scan, and exact-candidate Integration Gate. Any unverified host-runtime behavior remains explicitly unverified.
