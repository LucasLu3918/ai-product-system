# Scenario 146 — Evolution Radar Local Deterministic Pre-analysis

Evolution Radar must provide useful first-pass triage without requiring an external Agent/model API key.

Expected:

- operate only on already-collected Evolution Radar evidence, signal titles/metadata, configured deterministic rules, and the source-controlled Capability Map;
- require no external Agent/provider credential;
- perform no additional external network call;
- produce deterministic topic-category hints and matched AIPS capability hints;
- detect bounded near-duplicate title clusters with a deterministic token/Jaccard rule;
- compute a deterministic Human review priority (HIGH / MEDIUM / LOW) from declared rule weights, capability matches, and recurrence only;
- preserve every semantic recommendation as `ANALYSIS_PENDING`; local pre-analysis must not emit COVERED/HOLD/ASSESS/TRIAL/ADOPT or mutate recommendation state;
- explicitly report `semantic_suitability_inferred=false` and `recommendation_state_mutated=false`;
- bind output to the exact repository revision, evidence digest, local-preanalysis config digest, and Capability Map digest;
- keep provider-neutral semantic handoff available for later Human-selected semantic analysis;
- include the deterministic pre-analysis in the Human review Issue without granting implementation, PR, merge, release, publication, or Human-decision authority;
- produce identical output for identical evidence/config/capability inputs.
