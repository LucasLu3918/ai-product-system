---
id: llm-feature-integration
description: Design product LLM features with explicit schemas, quality evaluation,
  threat controls, latency budgets and cost limits.
capability: engineering
estimated_context_cost: medium
triggers:
- llm_feature
- ai_assistant_in_product
- rag_pipeline
- prompt_design
model_requirements:
  reasoning: high
  coding: strong
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# LLM Feature Integration

Use for AI capabilities inside a user-facing product. For changes to AIPS agent behavior, follow orchestration/SYSTEM_SELF_IMPROVEMENT.md. Load threat-modeling for the broader product threat model and orchestration/SECRET_HANDLING.md for credentials.

## Method

1. Define the user task, permitted data, quality target, failure behavior, latency budget, and cost envelope. Identify whether the feature needs generation, retrieval, tools, or a deterministic alternative.
2. Keep system instructions, untrusted user or retrieved content, and tool results in distinct trust boundaries. Treat all user-supplied and retrieved text as data, not authority. Restrict tools by least privilege and validate authorization in application code.
3. Use a typed or schema-constrained response where downstream code depends on structure. Validate it, handle refusal, truncation, malformed output, timeout, and provider failure explicitly.
4. For retrieval, specify source authorization, freshness, chunking, citations, deletion propagation, and behavior when evidence is absent. Do not let retrieved content override policy.
5. Build a representative, versioned offline evaluation set before launch. Include normal, ambiguous, adversarial, privacy, and failure cases; define task-specific quality and safety thresholds and compare changes against a baseline.
6. Estimate token volume, model calls, retries, retrieval, and storage. Measure latency and cost under realistic traffic; define rate limits, caching, fallback, and spend alerts where appropriate.
7. Recheck model IDs, capabilities, and prices from current provider sources at decision time. Keep secrets in the approved secret store and out of prompts, logs, fixtures, and reports.

## Output

Provide the prompt/tool or retrieval design, output contract, trust boundaries, evaluation set and pass thresholds, failure handling, model-selection rationale, and measured or estimated cost/latency with assumptions. Do not claim an LLM feature is reliable from prompt review alone.
