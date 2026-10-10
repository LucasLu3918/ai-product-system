---
id: product-research
description: Research product, market and domain evidence to support planning decisions and explicit
  assumptions.
capability: product
estimated_context_cost: medium
triggers:
- market_research
- competitor_research
- product_benchmark
- user_problem_research
- industry_research
- product_strategy_evidence
model_requirements:
  reasoning: high
  coding: none
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Product Research

Produce evidence-backed product and market research that informs product decisions. Do not substitute model memory for current evidence.

## Positive triggers

- market research or competitor analysis informs a product decision;
- the user asks for user needs, industry evidence or product benchmarks;
- a material product assumption needs external evidence.

## Non-triggers

- visual reference research (use `creative-reference-research`);
- technology selection, infrastructure benchmarking or financial modeling;
- general web search without a product decision to inform;
- project-specific source caching (use Project Intelligence when appropriate).

## Inputs

Product problem, target users, research questions, known constraints, market/geography and desired evidence depth. Ask for a blocking market choice only when a safe default cannot be recorded as an assumption.

## Method

1. Convert the product problem into bounded research questions and name the decision each question informs.
2. Search current, relevant sources. Prefer primary sources for policies, official product behavior and published data; use independent sources to corroborate market interpretation.
3. Record source title/URL, publisher, observed date, evidence type, relevant passage or data point, geography and limitations.
4. Separate `FACT`, `OBSERVATION`, `INFERENCE`, `RECOMMENDATION`, `ASSUMPTION` and `UNKNOWN`.
5. Compare alternatives on stated dimensions; explain missing evidence, freshness and confidence. Do not infer demand from competitor feature presence alone.
6. Translate supported observations into product implications and unresolved decisions.

## Output

Use `templates/planning-package/PRODUCT_RESEARCH.md`. Research supports decisions; it does not make product or human approval decisions. Load domain reference packs only when they apply, and treat their patterns as options rather than mandatory product rules.

## Game playtesting

When evaluating a game experience, convert the design assumption into an observable research question. Recruit a small, relevant range of players; explain the session, obtain consent, and collect only data needed for the question. A small qualitative sample reveals usability and comprehension issues but does not estimate population rates.

Use think-aloud selectively so narration does not distort time-sensitive play. Observe first-time user experience (FTUE), task completion, confusion, retries, quits, and recovery. Ask neutral questions after the task; do not coach players through the moment being evaluated. With permission, use minimal event telemetry to understand funnels and drop-off, and protect identifiers and session recordings.

Report the participant/context, task, observed behavior, direct quotes only with consent, interpretation, limitations, and the next testable change. Separate observation from designer inference; do not label a player as the cause of a design failure.
