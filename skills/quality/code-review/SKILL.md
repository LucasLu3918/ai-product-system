---
id: code-review
capability: quality
estimated_context_cost: low
---

# Code Review

Review against user intent, applicable project instructions, contracts, correctness, regression risk, tests, maintainability, security and performance where relevant.

For large/core/high-risk changes, use `orchestration/MULTI_REVIEW.md` to split specialist perspectives instead of making every reviewer inspect everything.

Material findings must include evidence, impact and recommendation. Do not invent new scope during review.

After the Author fixes findings, prefer targeted re-review of the finding + diff + affected tests unless the boundary materially expanded.

Outcomes: PASS, PASS WITH COMMENTS, REQUEST CHANGES, BLOCK.
