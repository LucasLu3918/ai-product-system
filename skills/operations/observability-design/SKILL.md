---
id: observability-design
description: Design actionable, privacy-safe logs, metrics, traces, SLOs and alerts
  before a service launches.
capability: operations
estimated_context_cost: low
triggers:
- new_service_launch
- slo_definition
- alerting_design
model_requirements:
  reasoning: high
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Observability Design

Use before launch or when changing a service’s operational signals. For an active incident, use incident-response; link its response runbook to the signals and dashboards designed here. Prefer provider-neutral instrumentation until deployment constraints are known.

## Method

1. Identify critical user journeys, dependencies, failure modes, and the owner who can act on each alert.
2. Specify structured logs with correlation IDs, event names, outcome, and bounded timing fields. Exclude secrets, credentials, full payment data, and unnecessary personal data.
3. Define metrics for traffic, errors, latency, saturation, and domain outcomes. Use bounded-cardinality labels; never put user IDs or unbounded request values in metric labels.
4. Define SLI numerator/denominator and time window, then set an SLO from user needs and system capability. State the error budget and how it changes release or incident decisions.
5. Alert on actionable user impact or fast error-budget burn. Give each alert a severity, owner, runbook, and deduplication strategy; dashboards alone are not alerts.
6. Add health checks and traces where they improve diagnosis. Set retention and access based on data sensitivity.
7. Exercise signals with representative success and failure paths before launch.

## Output

Provide event/log fields, metrics and labels, SLI/SLO definitions, alert thresholds and owners, dashboards/runbooks, retention, and verification cases. Avoid vendor selection without concrete hosting and operations constraints.
