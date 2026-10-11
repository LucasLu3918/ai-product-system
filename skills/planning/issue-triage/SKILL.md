---
id: issue-triage
description: Classify an issue from supplied evidence and produce a reproducible, decision-ready handoff without changing the tracker.
capability: delivery-planning
estimated_context_cost: low
triggers:
- explicit_issue_triage_request
- issue_reproducibility_review
- issue_priority_assessment
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Issue Triage

Use this Skill when the user asks to assess an issue or prepare it for engineering work.

1. Summarize the reported behavior and separate observed facts from assumptions.
2. Check whether the report includes a minimal reproduction, expected/actual behavior, environment and relevant evidence.
3. Identify likely affected area, severity rationale, missing information and a proposed next action.
4. Produce a concise handoff with a suggested category or priority only when evidence supports it.
5. Keep labels, assignment, comments, status changes and issue creation as proposals unless the user explicitly authorized the exact tracker write.

Do not infer severity from tone, expose private reports, or close an issue without evidence and authorization.

Source note: adapted from mattpocock/skills engineering/triage at 49dd158d1076134a641b33efb035946536778336 (MIT); see licenses/MIT-Matt-Pocock-Skills.txt.
