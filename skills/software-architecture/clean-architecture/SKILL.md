---
id: clean-architecture
capability: software-architecture
applies_when:
  - dependency_boundaries_matter
  - domain_logic_should_be_framework_independent
  - architecture_review
estimated_context_cost: low
---

# Clean Architecture

Use dependency direction and boundary separation, not a mandatory folder template.

Rules:

- domain/business policy must not depend on delivery frameworks, databases, queues, cloud SDKs or UI frameworks;
- application/use-case code coordinates business behavior and ports;
- infrastructure implements outward-facing adapters;
- dependencies point toward stable business policy;
- keep simple systems simple: do not create interfaces, DTOs, mappers or layers with no demonstrated value;
- in brownfield work, improve boundaries incrementally inside the approved change boundary.

Review questions:

1. Did infrastructure leak into core business rules?
2. Is a new abstraction solving a current dependency problem or only adding ceremony?
3. Can the core behavior be tested without external infrastructure?
4. Does the change preserve project conventions where they remain adequate?
