---
id: grill-with-docs
description: Explicitly interview me about a plan or domain model, then prepare a project glossary and ADR draft when the decisions are clear.
capability: product
estimated_context_cost: medium
triggers:
- explicit_grill_with_docs
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
---

# Grill with Docs

Use only when the user explicitly invokes `$grill-with-docs` or directly asks to run this workflow. Do not start it for ordinary planning, domain, glossary, or ADR requests; route those to the existing AIPS Skills.

Interview the user to resolve the plan or domain model, then prepare a glossary and/or ADR from decisions that were actually established. Keep the interview separate from implementation: this Skill does not authorize code changes, external actions, or publication.

## Interview

1. Inspect relevant project instructions and existing glossary/ADR conventions before proposing document locations or formats.
2. Ask one decision-focused question at a time. Include a recommended answer and the consequence of choosing it when that helps the user decide. Use verified project evidence to answer factual questions; do not invent domain facts.
3. Distinguish settled decisions from assumptions, open questions, and alternatives. Revisit earlier conclusions when a new answer changes them.
4. Stop when the user asks to stop or when remaining decisions can be recorded clearly as open questions. Summarize the decisions and unresolved points before drafting.

## Documents

- Create a glossary entry only for a term whose meaning or boundary is important to the shared model. Prefer the project's existing glossary and preserve its format.
- Create an ADR only for a consequential technical or domain decision. Follow the existing ADR location and template. Use AIPS `architecture-decision-record` guidance; an ADR records rationale and does not grant approval.
- If a term is ambiguous across contexts, use AIPS `domain-driven-design` guidance proportionately. Do not impose DDD structure on a simple domain.
- Show the proposed glossary and ADR changes to the user before writing. Apply them only after the user approves the proposed documents or has directly requested their creation in this task. Resolve the repository's Change Impact requirements before any project mutation.
- Do not overwrite user edits. Re-read target files before each write and make the smallest change that preserves surrounding content.

Finish with a concise list of settled decisions, document paths changed, and open questions. If no consequential decision or useful glossary term emerged, explain why a document would add no value and leave files untouched.
