# Scenario 131 — Structural Retrieval Adoption

After a bounded Structural Retrieval candidate has passed controlled Trial evidence and Human Adoption Decision, AIPS uses the built-in exact-identifier two-hop relation graph in normal Retrieval Intelligence.

The adopted behavior must:

- enable Structural Retrieval by default for normal `aips intelligence retrieve` and Turn Context retrieval;
- preserve an explicit `--no-structural` diagnostic opt-out that disables only the structural lane;
- keep the lane local, deterministic, provider-neutral and free of external parser/LSP dependencies;
- discover bridge chunks through the existing lexical index rather than an unbounded full-repository scan;
- resolve outgoing identifiers through the indexed symbol table with hard bridge/identifier/target/test limits;
- expose structural status, default/enabled selection and traversal telemetry in retrieval evidence;
- preserve token budgets, revision/content provenance, secret filtering and semantic-provider truthfulness;
- keep Retrieval Quality Evaluation on the adopted default behavior while retaining Scenario 130 as explicit OFF/ON Trial replay evidence;
- introduce no new Role, Skill, Human Approval Gate or publication authority.
