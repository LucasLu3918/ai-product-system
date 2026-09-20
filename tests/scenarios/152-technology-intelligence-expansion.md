# Scenario 152 — Technology Intelligence Expansion

## Intent

Evolution Radar MUST broaden weekly technology discovery without turning source volume, forum popularity or optional model access into adoption authority.

## Expected behavior

- configure at least six public community sources and retain primary/vendor sources as a separate evidence role;
- consider weekly community coverage healthy when at least five community sources successfully contribute evidence;
- treat best-effort source failures as explicit degraded evidence rather than fabricating replacements;
- collect no more than eight candidates from any single source and no more than 50 raw signals globally;
- apply the global cap deterministically with round-robin source fairness so early configured sources cannot monopolize the budget;
- preserve every signal's source IDs and source roles across exact-fingerprint deduplication;
- label community-only evidence as DISCOVERY_ONLY, primary-only evidence as PRIMARY_SOURCE, and cross-role recurrence as PRIMARY_CORROBORATED;
- run credential-free deterministic pre-analysis over the bounded evidence;
- cap the Human shortlist at 12 and the semantic-analysis queue at 10, suppressing near-duplicate titles from consuming semantic slots when another candidate is available;
- permit no more than five ASSESS/TRIAL/ADOPT semantic recommendations in one bounded analysis;
- leave every signal outside the semantic queue at ANALYSIS_PENDING;
- reject ADOPT when a signal is supported only by community discovery evidence and has no primary-source role;
- keep scheduled semantic providers optional and preserve provider-neutral handoff when no external model credential exists;
- preserve contents:read + issues:write research permissions and grant no implementation, PR, merge, release, publication or Human-decision authority.

## Rationale

Community forums are discovery channels, not governance authorities. The bounded 50 → 12 → 10 → 5 funnel increases research breadth while constraining review cost, semantic-token exposure and recommendation noise. Primary corroboration prevents popularity from being mistaken for adoption evidence.
