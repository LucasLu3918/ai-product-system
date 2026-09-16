# Quality Planning

Use for complete products and material product plans to turn vague quality expectations into risk-proportional, testable targets.

## Quality classes

Use one baseline, then adjust individual dimensions independently.

- **Q1 — Lightweight**: personal tools, static sites, demos, low-risk internal tools.
- **Q2 — Standard**: typical SaaS, member platforms, B2B systems, production commercial websites.
- **Q3 — Critical**: payments/stored value, high-sensitivity data, high-availability systems, major operational/financial impact.

A Q2 product may have Q3-level security while keeping medium performance requirements. Do not treat the class as one rigid bundle.

## Seven dimensions

Every complete product evaluates:

1. Performance
2. Security
3. Usability
4. Reliability
5. Maintainability
6. Resource / Cost
7. Delivery Time

An item may be `N/A` only with a reason.

## Discovery

Use three rounds rather than a large questionnaire.

### Round 1 — product importance and constraints

Resolve only information that materially affects the profile:

- primary user type;
- expected scale;
- failure impact;
- data sensitivity / auth / economic value;
- delivery preference: prototype / balanced MVP / production-first / critical-quality;
- operations preference: low maintenance / balanced / low infra cost / high control;
- explicit deadline or cost ceiling when known.

Do not ask users to invent p95 latency, RTO, RPO or SLO numbers when they do not know them.

### Round 2 — conditional questions

Ask only when applicable, for example:

- real-time / streaming;
- mobile/tablet/browser requirements;
- accessibility requirements;
- multi-region / 24x7;
- fixed deadline/budget;
- compliance/audit/retention;
- external vendor dependencies;
- queues/background jobs.

### Round 3 — propose the profile

The Agent derives a draft `QUALITY_PROFILE.yaml` with:

- priority per dimension;
- measurable target or explicit qualitative acceptance rule;
- verification method;
- assumptions and confidence;
- N/A reasons;
- trade-offs.

Show only material recommendations/unknowns to the user.

## Targets and evidence

Prefer:

~~~text
Requirement
→ Target / Budget
→ Implementation implication
→ Verification method
→ Evidence
~~~

Examples:

- “fast” → p95 API latency target + benchmark/load test;
- “secure” → SAL/security requirements + security evidence;
- “usable” → responsive/accessibility/critical-flow criteria + UX/E2E evidence;
- “reliable” → availability/recovery/backup targets + recovery evidence;
- “maintainable” → complexity/test/documentation expectations + architecture/code review;
- “affordable” → cost envelope/TCO assumptions + refined estimate;
- “quick delivery” → range + confidence + dependencies.

## Estimates

Do not provide fake precision.

Use:

- optimistic;
- expected;
- risk-adjusted;
- confidence.

Estimate at least twice for substantial products:

1. initial estimate before architecture;
2. refined estimate after architecture/dependency decisions.

Cost should consider Total Cost of Ownership (TCO), including infrastructure, managed services, engineering maintenance, upgrades and operational complexity.

## Budgets

Use budgets when useful:

- performance budget;
- cost budget;
- delivery budget;
- complexity budget;
- reliability/recovery budget.

Budgets constrain overengineering; they are not universal numeric defaults.

## Trade-offs

When quality dimensions conflict, apply:

~~~text
Hard external/safety/legal constraints
→ data integrity/security hard requirements
→ explicit user/business priorities
→ critical success criteria
→ reliability/recoverability
→ maintainability/lifecycle cost
→ performance optimization
→ cost/delivery optimization
~~~

This is a decision framework, not a universal ranking. Record material trade-offs and accepted compromises.

## Observability planning

Observability supports reliability/operations; it is not a separate quality class.

Plan needs before selecting vendors:

- structured application logs;
- health checks;
- metrics;
- traces;
- dashboards;
- alerts;
- audit logs where required.

Production baseline: structured logs + health check.

Metrics/dashboard/alerts/tracing are risk-proportional.

High-value/security-sensitive actions may require separate audit logs with stronger retention/access/integrity requirements.

Keep instrumentation provider-neutral where practical. Select ELK/Loki/Prometheus/Grafana/OpenTelemetry/managed services after the target production environment and operations constraints are known.

## Output

Persist the active profile using `templates/quality/QUALITY_PROFILE.yaml`.

For a product workspace, prefer:

`docs/quality/QUALITY_PROFILE.yaml`

Link it from PRODUCT.yaml / planning index when applicable.
