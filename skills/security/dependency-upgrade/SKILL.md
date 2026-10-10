---
id: dependency-upgrade
description: Prioritize dependency updates by exploitability and supply-chain risk,
  then verify compatibility and lockfile changes.
capability: security
estimated_context_cost: low
triggers:
- vulnerability_audit_report
- major_version_upgrade
- new_dependency_proposal
model_requirements:
  reasoning: medium
  coding: normal
  reliability: high
  minimum_tier: 2
  preferred_tier: 2
---

# Dependency Upgrade

Use for vulnerability findings, planned version upgrades, or proposed new dependencies. Keep security fixes distinct from unrelated feature changes when that improves review and rollback.

## Method

1. Identify the exact package, direct/transitive path, runtime or development exposure, supported version range, and affected code path.
2. Rank findings by severity, reachability, exploit conditions, available fix, and exposure. Treat scanner severity as evidence, not a substitute for contextual risk.
3. Read the official advisory, release notes, and migration guide for the target version. For a new package, review provenance, maintainer activity, license, install behavior, namespace-confusion risk, and transitive footprint.
4. Prefer the smallest supported safe version. Separate major upgrades and record breaking changes; do not silently replace a package with an unreviewed alternative.
5. Review the complete lockfile diff and source/registry. Use project-pinned tooling and approved official registries; do not execute untrusted installation scripts.
6. Run the affected tests, build, security scan, and compatibility checks. Report any unresolved advisory and compensating control.

## Output

Provide package paths, risk rationale, target versions, lockfile impact, breaking changes, commands and results, and remaining exposure. Do not claim an upgrade is safe from a version bump alone.
