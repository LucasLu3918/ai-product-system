# Model Routing

The system is provider-neutral. Skills describe capability needs; the Model Router maps an execution profile to models available on the current platform.

## Principle

Use **minimum sufficient intelligence**: choose the lowest-cost eligible model that can reliably complete the bounded task. Optimize total task cost, not single-call price.

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
  coding: medium
  reliability: high
  minimum_tier: 2
  preferred_tier: 3
```

Hints are aggregated across selected skills. They do not choose a concrete model and do not override privacy, risk or governance.

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

See `schemas/execution-profile.yaml`.

## Primary agent and subagents

Choose a model independently for the primary agent and each bounded subagent. Do not inherit the primary model automatically.

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

Start at the resolved minimum sufficient tier. Escalate when new evidence shows insufficient reasoning, higher risk, larger context or repeated unreliable results. De-escalate after the difficult decision is resolved when the remaining work is routine.

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
