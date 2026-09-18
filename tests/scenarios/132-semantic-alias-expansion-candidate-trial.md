# Scenario 132 — Semantic Alias Expansion Candidate Trial

After Structural Retrieval adoption, AIPS evaluates a dependency-free deterministic alias-expansion candidate before introducing an embedding model, Vector DB or remote semantic provider.

The committed Trial outcome is **FAIL / HOLD**. Scenario 132 exists to make that negative evidence reproducible rather than tuning the candidate until CI turns green.

The replay must:

- keep current v0.23 default retrieval, including Structural Retrieval, as the baseline;
- enable only the transparent version-controlled software-engineering alias expansion lane in the candidate run;
- keep `semantic.status=NOT_CONFIGURED` because no semantic/embedding provider executes;
- expose matched alias groups, expanded terms and group-membership evidence;
- reproduce the observed required-case regressions for auth-token-expiry, Go receipt reconciliation and TypeScript session refresh;
- reproduce the source-recall regression for the already-covered registration diagnostic;
- keep `synonym-access-rotation` as an unresolved semantic target with no source-recall improvement;
- return non-zero Trial status with recommendation `HOLD`;
- keep alias expansion disabled by default and introduce no Embedding, Vector DB, Tree-sitter/LSP or remote-provider dependency;
- preserve automatic_adoption=false and automatic_embedding_provider_enablement=false;
- require Human review before a different semantic retrieval candidate is researched or adopted.

A future improvement to the alias candidate must intentionally update this Scenario and evidence contract; silently converting the known HOLD into PASS is not allowed.
