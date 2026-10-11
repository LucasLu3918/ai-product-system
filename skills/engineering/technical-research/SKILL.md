---
id: technical-research
description: Investigate technical APIs, standards, frameworks and architecture choices with current primary-source evidence.
capability: engineering
estimated_context_cost: medium
triggers:
- technical_research_request
- framework_api_question
- standards_comparison
- technology_choice_evidence
model_requirements:
  reasoning: high
  coding: none
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Technical Research

Use current evidence to resolve a technical question or support an explicit engineering decision.

## Method

1. Define the question, the decision it informs, the repository/runtime version and constraints.
2. Prefer official documentation, standards, release notes and source code for behavior claims. Use independent sources to corroborate when primary sources are incomplete.
3. Record the source title, URL, publisher, version or revision, observed date and the claim it supports.
4. Separate confirmed behavior from inference, recommendation, assumption and unknown.
5. Compare options against the stated constraints. Call out version differences and missing evidence.
6. Return a concise result with citations and a suggested next step. Save a research note only when the user asks for a file or the project workflow requires one.

Do not present remembered details as current documentation. Do not claim that a source was checked unless it was actually opened. Research informs the decision; it does not authorize dependency changes, external writes or production changes.

Source note: adapted from mattpocock/skills engineering/research at 49dd158d1076134a641b33efb035946536778336 (MIT); see licenses/MIT-Matt-Pocock-Skills.txt.
