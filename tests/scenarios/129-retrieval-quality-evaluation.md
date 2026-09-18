# Scenario 129 — Retrieval Quality Evaluation

AIPS can evaluate Retrieval Intelligence with a reproducible, provider-neutral suite before deciding whether another retrieval technology should be added.

The evaluation must:

- compare bounded v0.21 local hybrid retrieval against an explicitly declared v0.20-style static topic-context baseline;
- use repository-specific expected relevant source paths and optional expected Git-history terms rather than subjective quality labels;
- compute Precision@K, Recall@K, F1@K, MRR, history recall, irrelevant-context rate, token usage and direct-source-recall delta deterministically;
- record observed latency as informational evidence only and never make CI depend on wall-clock improvement;
- bind the suite and output to deterministic fingerprints while preserving repository/index provenance;
- distinguish direct source evidence from a static topic merely mentioning the same path;
- keep the comparison scope limited to task-specific repository evidence retrieval and not claim overall Agent task-completion superiority;
- distinguish `required` regression cases from `diagnostic` stress cases: required failures block the suite, while diagnostic failures remain explicit GAP evidence without failing the overall release gate;
- aggregate diagnostic gaps by declared dimensions such as language, low lexical overlap, cross-file call chain, monorepo/shared module, or structural retrieval;
- produce PASS / FAIL from declared thresholds without automatically enabling a semantic provider, changing ranking weights, or selecting Tree-sitter/LSP/Sourcegraph/embedding technology;
- require Human review before any next retrieval-architecture optimization.
