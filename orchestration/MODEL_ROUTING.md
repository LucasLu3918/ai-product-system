# Model Routing

The system is provider-neutral. Skills describe capability needs; the Model Router maps an execution profile to models available on the current platform.

## Principle

Preserve the eligible runtime/user-selected primary implementation model. Apply **minimum sufficient intelligence** to auxiliary work: choose the lowest-cost eligible helper/reviewer that can reliably complete its bounded task. Optimize total task cost, including context duplication and reconciliation. A capability or policy mismatch requires an explicit explanation; never silently downshift the primary implementer because a Skill has a lower preferred tier.

## Intelligence tiers

- **Tier 1 — Lightweight**: discovery, metadata, formatting, simple classification.
- **Tier 2 — Standard**: routine coding, CRUD/API changes, unit tests, ordinary reviews.
- **Tier 3 — Advanced**: architecture, DDD, performance, concurrency, database design, complex debugging.
- **Tier 4 — Critical Reasoning**: high-impact security, financial correctness, irreversible migration, difficult distributed consistency or other critical decisions.

Adapters map these tiers to currently available models. Core files never hard-code provider model names.

## Routing factors

Consider together:

1. policy/provider eligibility;
2. data sensitivity and privacy;
3. required tools/modalities;
4. business impact;
5. technical complexity;
6. failure/security/irreversibility risk;
7. Effective Security Assurance Level and Reliability Impact;
8. reasoning and coding requirement;
9. context complexity;
10. reliability requirement;
11. expected total cost.

Business impact is a factor, not a shortcut to a stronger model. Critical risk may impose a minimum tier regardless of weighted cost preference.

## Skill hints

A selected skill may declare hints such as:

```yaml
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
```

Canonical routing metadata lives in each `SKILL.md` frontmatter. `scripts/skill_index.py --write` generates the compatible v1 `skills/INDEX.yaml`; its default read-only check rejects drift. Migrate positive `applies_when` aliases into `triggers`. Prose explains applicability and non-triggers; it is not a second machine routing rule.

Hints are aggregated across selected skills. They do not choose a concrete model and do not override privacy, risk or governance. Retained `minimum_tier` / `preferred_tier` fields support existing consumers and auxiliary eligibility; a preference is not a ceiling on the selected primary model.

## Execution profile

Before execution, resolve a compact profile:

```yaml
business_impact: medium
technical_complexity: high
risk: elevated
security_assurance: 3
reliability_impact: 3
reasoning: high
coding: strong
reliability: high
context: small
data: internal
preferred_tier: 3
minimum_tier: 2
```

See `schemas/execution-profile.yaml`. The following optional policy fields document execution intent without changing host settings or naming providers:

```yaml
primary_execution_policy:
  strategy: runtime_preferred
  allow_downshift: false
auxiliary_routing:
  strategy: minimum_sufficient
```

Legacy profiles without these fields use the same primary-preserving policy. Privacy, tool eligibility and critical capability floors still apply. If the host cannot select an auxiliary model, report the limitation and use the eligible current model or a deterministic tool; do not claim a model switch.

## Primary agent and subagents

Keep the runtime/user-selected primary implementation model when eligible. First solve a bounded implementation with the primary agent. File count or model availability alone does not justify delegation. Delegate only when parallel evidence gathering, specialized risk analysis, context isolation or required independent review materially improves the result. Prefer deterministic tools for listing files, parsing data and running checks.

Resolve each justified auxiliary agent independently; do not inherit the primary model automatically. Preserve any host/user constraints on model selection.

A subagent must have:

- one clear objective;
- an explicit scope;
- selected role/skills;
- the smallest useful context;
- an expected output;
- explicit tool/write permissions.

Do not delegate vague work such as "review everything". Analysis/review subagents may run in parallel; the single-writer rule still applies to each change boundary.

## Subagent context isolation

Do not copy the primary agent's entire context to every subagent. Pass only task-relevant instructions, project evidence and selected skill bodies.

Example:

```yaml
objective: "Identify the dominant SQL latency source"
role: database-engineer
skills: [sql-performance]
scope:
  - repository/order_repository.go
  - schema/orders.sql
permissions:
  read: true
  write: false
expected_output:
  - measured bottleneck
  - evidence
  - recommendation
```

## Escalation and de-escalation

Auxiliary work starts at the resolved minimum sufficient tier. Escalate when new evidence shows insufficient reasoning, higher risk, larger context or repeated unreliable results. De-escalate auxiliary work after the difficult decision is resolved when the remainder is routine. Primary downshift requires an explicit user decision; a lower-cost hint is not permission. A policy/capability mismatch blocks affected work until an eligible route is resolved.

A subagent must request escalation instead of guessing beyond its competence.

## Security assurance interaction

SAL is an assurance requirement, not a model tier.

Typical routing guidance:

- SAL 0–1: no dedicated high-tier Security Reviewer by default;
- SAL 2: security review commonly Tier 2–3 when the affected boundary warrants it;
- SAL 3: Security Reviewer normally minimum Tier 3;
- SAL 4: Security Reviewer Tier 3–4; critical financial/integrity/security decisions may require Tier 4.

The Router still considers privacy, task complexity, tools, context and total cost. A cosmetic low-impact change in a SAL 4 product can remain low-tier when it does not touch the protected boundary.

## Reviewer routing

Reviewer tier is resolved independently from author tier. A simple implementation may still require a stronger reviewer when hidden failure modes are costly; documentation or cosmetic review may use a lower tier.

For Multi-Perspective Review, route each reviewer independently by its bounded perspective. Do not copy the full author context to every reviewer. Prefer parallel read-only analysis and cap reviewer count to the smallest set covering the material risks. Targeted re-review may use smaller context and, only when the remaining risk/capability floor permits it, a lower tier. Required independence is preserved even when author and reviewer use the same model; author self-check is not independent review.

## Budget guidance

Use qualitative budgets rather than provider-specific token numbers:

```yaml
budget:
  context: small
  reasoning: medium
  max_parallel_subagents: 3
  prefer_cost_efficient: true
```

Increase budget only when evidence shows the current allocation is insufficient.
