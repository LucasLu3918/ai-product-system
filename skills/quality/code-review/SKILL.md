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
## Standards and specification lenses

For a material review, pin one exact base and review the same candidate through two independent questions: does the change follow documented project standards, and does it satisfy the originating request or specification? Cite the applicable file, line or test for each finding. When no specification is available, mark that lens unavailable rather than inventing requirements. Keep the axes distinct so a standards pass cannot hide a behavior mismatch. Use the repository's multi-review workflow when its risk policy requires specialist review; never imply that separate agents ran unless they actually did.

Source note: adapted from mattpocock/skills engineering/code-review at 49dd158d1076134a641b33efb035946536778336 (MIT); see licenses/MIT-Matt-Pocock-Skills.txt.
