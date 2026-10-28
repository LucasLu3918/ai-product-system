# 275. Optional per-project governance modes

## Scenario

AIPS can be installed without taking over a project's native development flow. A user may opt a repository into `observe`, `assist`, or explicitly scoped `enforce`; a repository with no external mode record remains `off`.

## Acceptance criteria

- Missing configuration resolves to `off` without creating repository files or user configuration.
- `aips project mode show|set` stores the opaque repository identity, selected mode, and optional scope under the user's XDG AIPS configuration.
- Mode storage is outside the repository, private, atomic, schema-validated, and rejects symlinked or corrupt records.
- `observe` and `assist` add only safe advisory context; neither returns a host allow/deny decision.
- Hard content safety findings remain blocking in every project mode and cannot be downgraded by `assist`.
- `enforce` requires a non-empty allowlisted action scope. Out-of-scope actions are not blocked by project policy; failed checks block only in-scope actions.
- The independent runtime policy, global administrator high-assurance trust root, protected AIPS installation paths, and native GitHub protections cannot be weakened by project mode.
- A mode record never stores the raw remote URL or project contents.

## Evidence

- `scripts/project_governance_mode.py`
- `scripts/governance_guard.py`
- `scripts/aips_cli/project.sh`
- `scripts/aips_cli/dispatch.sh`
- `tests/test_project_governance_modes.py`
- `tests/validation/project_governance_modes_contracts.py`
