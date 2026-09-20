# Scenario 153 — Evolution Evidence Quality and Primary Corroboration

## Intent

Evolution Radar MUST distinguish discovery popularity from deterministic evidence strength before semantic recommendations can progress to advisory ADOPT.

## Expected behavior

- preserve exact multi-source provenance for every deduplicated signal;
- deterministically classify evidence strength on a 0–4 scale:
  - level 0 = single-community discovery only;
  - level 1 = multi-community recurrence without a primary source;
  - level 2 = at least one primary/vendor source;
  - level 3 = primary source plus community corroboration;
  - level 4 = multiple independent primary sources;
- record primary/community source counts as evidence metadata owned by deterministic AIPS code;
- preserve evidence quality across monthly and quarterly durable rollups;
- expose the evidence level to credential-free pre-analysis and apply only a bounded priority bonus;
- bind the semantic package to the deterministic minimum ADOPT evidence level;
- reject advisory ADOPT when a selected signal is below level 2;
- allow primary-source level 2+ evidence to be semantically assessed for ADOPT without granting implementation authority;
- prevent semantic providers from inventing or upgrading evidence strength;
- keep all evidence/recommendation outputs advisory and preserve Human Decision, implementation, merge, release and publication authority boundaries.

## Rationale

Community sources are useful discovery channels, but recurrence or popularity is not equivalent to technical verification. A deterministic evidence-quality layer makes source confidence explicit and reviewable before semantic reasoning or Human adoption decisions.
