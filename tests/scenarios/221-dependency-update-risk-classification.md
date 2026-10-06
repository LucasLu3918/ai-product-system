# Scenario 221 — Dependency Update Risk Classification

Dependency update classification maps known packages and GitHub Actions to an explicit risk class and recommended validation plan. Unknown packages fail closed to `UNCLASSIFIED` / `HIGH` and require human review. Semantic runtime updates require retrieval regression evaluation and a semantic trial. Classification is advisory evidence only: dependency updates and policy changes never auto-merge or gain automatic approval.
