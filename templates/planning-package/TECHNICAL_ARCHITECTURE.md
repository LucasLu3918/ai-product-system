# Technical Architecture

## Context & Constraints

## Quality Profile

- Quality class:
- Performance targets:
- Security assurance:
- Usability/accessibility:
- Reliability / recovery:
- Maintainability / complexity budget:
- Resource / TCO envelope:
- Delivery constraints:

## System Context

~~~mermaid
flowchart LR
    U[User] --> A[Application]
~~~

## Components / Boundaries

## Architecture Profile

- Style:
- DDD level:
- Dependency rules:

## Data Model

## Integrations

## Security Assurance

- Product Baseline SAL:
- Reliability Impact:
- Critical security floors:
- Protected assets:

## Security / Trust Boundaries

## Performance / Scale Assumptions

## Observability Instrumentation

Plan requirements before provider selection.

- Structured logs:
- Health / readiness:
- Request / trace correlation:
- Metrics hooks:
- Trace hooks:
- Audit log:
- Sensitive data / redaction:
- Retention requirements:

## Deployment Units

| Unit | Type | Path / Repository | Runtime | Build / Test / Deploy independently? |
|---|---|---|---|---|

## Repository Strategy

- Strategy: monorepo / multi-repo
- Rationale:
- Cross-unit contract strategy:

## Environments

- Local:
- CI:
- Staging:
- Production:

## Runtime / Deployment

Concrete hosting/observability providers are selected during Production Enablement unless already known.

## Data Migration

- Required:
- Compatibility:
- Migration order:
- Verification:
- Recovery / rollback:

## Failure / Recovery / Rollback

## Resource / Cost / Time Estimate

### Initial
- Range:
- Confidence:
- Assumptions:

### Refined
- Range:
- Confidence:
- Architecture/dependency changes:

## Key Architecture Decisions
