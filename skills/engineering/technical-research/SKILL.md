---
id: technical-research
description: Research technical APIs and architecture using verifiable versioned sources.
capability: engineering
estimated_context_cost: medium
triggers:
- technical_source_research
- technology_api_evidence
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Technical Research

## Admission
Distinct from `product-research` (market/user evidence) and `creative-reference-research` (visual references). Inspired by Matt Pocock's `research`, without mandatory background-agent execution.

## Inputs and method
Define technical question, target environment/version, decision needing evidence, constraints, freshness horizon and permitted access. Prefer official documentation, standard/spec, maintained release notes and checked source. For each claim record URL/path, publisher, version/date, observed fact, limitation and confidence; verify nontrivial conflicts against independent evidence. Separate FACT, INFERENCE, RECOMMENDATION, ASSUMPTION and UNKNOWN. Produce concise Markdown in the project-selected location only when the change boundary permits it; otherwise report without writing.

## Boundaries
No speculative current API semantics, secret acquisition, new external paid provider, unattended background agent, or architecture decision without the existing ADR/Human approval process. Invoke `product-research` for market decisions.
