---
id: code-review
description: Review changes for correctness, security, maintainability and evidence against the
  declared change boundary.
capability: quality
estimated_context_cost: low
triggers:
- material_code_review
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Code Review

Review against user intent, applicable project instructions, contracts, correctness, regression risk, tests, maintainability, security and performance where relevant.

For large/core/high-risk changes, use `orchestration/MULTI_REVIEW.md` to split specialist perspectives instead of making every reviewer inspect everything.

Material findings must include evidence, impact and recommendation. Do not invent new scope during review.

After the Author fixes findings, prefer targeted re-review of the finding + diff + affected tests unless the boundary materially expanded.

Outcomes: PASS, PASS WITH COMMENTS, REQUEST CHANGES, BLOCK.

## Matt Pocock two-axis enhancement (standards and spec)

Pin a fixed comparison point (commit, branch, merge-base or approved change boundary) before reviewing. Independently evaluate:
1. **Standards:** project rules, maintainability, meaningful code smells, correctness, tests, safety and relevant performance.
2. **Spec:** requirement/issue acceptance criteria, missing behavior, scope drift and evidence of completion.

For nontrivial diffs, assign independent reviewer perspectives under `orchestration/MULTI_REVIEW.md`; never infer an independent review occurred without evidence. Aggregate findings with source path/line, severity, axis, reproducible evidence and recommended correction. After author fixes, re-review targeted changes plus impacted regression coverage. Standards/Spec PASS does not authorize publication or a merge.
