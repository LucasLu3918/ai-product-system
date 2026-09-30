# Implementation Resolution System Improvement Review

**Appropriateness:** Appropriate. API contracts and repository evidence need a reusable resolution boundary before implementation.

**User problem:** Produce idiomatic, quality-verified API implementation in existing or new projects without guessing contract authority, architecture, ownership, or project conventions.

**Proposed solution:** Add Implementation Resolution and Implementation Profile support for REST/OpenAPI and Go, PHP, Python, and .NET.

**Existing coverage:** Project Intelligence, REST API skill, requirement clarification, Planning Package, External Context Resolution, Quality Planning, scenario conformance, and existing Backend Engineer already cover parts of the workflow.

**Reuse / extension candidates:** Extend those canonical surfaces and preserve the existing Backend Engineer, skills, Change Impact, quality evidence, and Integration Gate.

**Lower-layer alternative:** A one-off task prompt would avoid global cost but would not preserve repeatable evidence or behavior across runtimes; extension at the orchestration/profile layer is the smallest reusable solution.

**Context / token cost:** One task-triggered protocol, one compact profile, and four concise profiles; load language/framework context on demand. No per-turn repository-wide scan or framework knowledge corpus.

**Security / reliability:** Protect unknown ownership; keep unresolved contract authority blocking; retain evidence provenance; no generator or external data transfer.

**Backward compatibility:** Additive. Existing project conventions and legacy workflows remain valid; no `.ai/` migration.

**Scenario / test impact:** Add 16 representative decision-boundary cases, deterministic structural checks, and lifecycle evidence; retain all existing scenarios.

**Human docs impact:** User Guide, Technology Guide, Architecture Overview, and Conformance.

**Agent docs impact:** Implementation Resolution, Project Intelligence, Requirement Clarification, External Context Resolution, Planning Package, Quality Planning, REST API skill, documentation sync and architecture.

**Architecture diagram impact:** YES. Resolution/Profile becomes a new stage between Project Intelligence/Planning and implementation roles.

**Constitution impact:** NO. Human Authority, safety boundaries, and publication authority do not change.

**Recommended AIPS solution:** Minimal reuse-first Resolution Foundation; no language roles, framework skills, generator adapters, new capability, or new approval gate.

**Additional optimization candidates:** Framework profiles and code generation are LATER; add only after demonstrated demand and evidence. No additional NOW optimization.

**Expected scope:** As enumerated in `IMPLEMENTATION_RESOLUTION_CORE_CHANGE_PROPOSAL.md`.

**Risks:** Scope expansion into code generation, stale framework knowledge, sparse-evidence over-classification, and project ownership collisions. Explicit non-goals, evidence provenance, on-demand official context, and deterministic ownership checks mitigate these risks.
