---
id: requirements-definition
capability: product
estimated_context_cost: low
---

# Requirements Definition

Turn accepted product intent into atomic, uniquely identified requirements with explicit scope, acceptance criteria and verification methods. Preserve EARS for observable functional behavior; use measurable targets and operating conditions for non-functional requirements.

For Planning Package v2, map every requirement to its acceptance IDs and declare each downstream artifact mapping as applicable with stable IDs or not applicable with a reason. Typical targets are UX screens, visual components, domain concepts, API operations, security controls and verification. Do not require irrelevant links for every requirement. Reuse `scripts/requirements_traceability.py` for the existing registry contract and `scripts/planning_package_validate.py` for manifest and cross-artifact structure. Passing structural checks does not prove the requirement is correct or that a planned test passed.

Mark source, priority, release and unresolved decisions. Do not invent product, user or market facts.
