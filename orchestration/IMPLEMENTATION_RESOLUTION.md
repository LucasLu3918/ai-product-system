# Implementation Resolution

## Purpose

Resolve how a requested change should be implemented before existing implementation roles write code. Produce an evidence-backed `Implementation Profile` from the requirement, project mode, contract authority, repository evidence, Human decisions, architecture, language/framework, ownership and quality requirements.

Resolution answers “what rules and boundaries apply to this change.” It does not implement the change, authorize an architecture migration, or modernize a framework.

## Trigger and inputs

Use when implementing or materially planning a REST API change from an API contract, especially when selecting among project patterns or languages. Inputs may include:

- clarified requirement and acceptance criteria;
- OpenAPI source and its authority decision;
- existing/new project mode;
- current Project Intelligence and task-relevant repository evidence;
- Human-confirmed technology and architecture decisions;
- version-specific official documentation when a material knowledge gap exists;
- ownership and project-native quality commands.

Resolve only decisions that materially affect the requested change. Reuse existing AIPS orchestration, Roles, Skills, Change Impact and Gate systems.

## Authority and invariants

- Human remains the final decision authority for new-project technology/architecture and contract-affecting changes.
- Explicit project rules and repeated project evidence outrank generic recommendations unless they conflict with higher authority, safety, an approved contract, or hard compatibility constraints.
- Existing architecture is evidence to preserve, not permission to migrate.
- `not_detected` is not `none`; absence of evidence is not evidence of absence.
- Logical architecture is separate from deployment architecture.
- OpenAPI DTOs are transport shapes, not automatically domain entities.
- Unknown ownership is protected. Generated boundaries do not own business decisions.
- No verification is `UNVERIFIED`, never `PASS`.
- The structural validator verifies representation only; semantic fit requires evidence and review.

## Resolution states

Use `confirmed`, `strong_evidence`, `inferred`, `not_detected`, `unresolved`, or `conflicting`. Attach a source/reference for each meaningful conclusion. Report conflicting sources instead of silently selecting one. An unresolved item declares whether it blocks this implementation and why.

## Flow

```text
Requirement Clarification
        ↓
Existing / New Project
        ↓
Project Intelligence / technology constraints
        ↓
Contract authority
        ↓
Architecture and deployment decisions
        ↓
Language / framework
        ↓
Version-aware knowledge
        ↓
Ownership and quality requirements
        ↓
Implementation Profile
        ↓
Existing implementation role / skills
        ↓
TDD → project-native verification → review
```

Use progressive disclosure. Do not run every resolver when existing evidence or a confirmed decision already answers the question.

## Existing-project flow

1. Refresh or use current Project Intelligence. Do not add a second scanner.
2. Inspect explicit project instructions, manifests, runtime/framework versions, toolchain commands, API specs, CI, tests, architecture/dependency evidence, generator configuration, and cross-cutting conventions relevant to the task.
3. Prefer the repository's documented build/test/format/lint commands over invented commands.
4. Sample the nearest same-module endpoint/use case and its tests; record evidence scope (`local`, `module`, `repository`, or `explicit_project_rule`). Do not treat one local example as a repository-wide rule.
5. Classify architecture only from evidence such as dependency direction, module boundaries, interface ownership and behavior location. A directory name alone cannot establish Clean Architecture or DDD.
6. Preserve project architecture. Raise a separate proposal if the requirement cannot be met safely within it; complexity assessment alone never authorizes migration.

## New-project flow

1. Apply hard constraints first; eliminate incompatible candidates.
2. Consider team fit, product/workload fit, ecosystem, existing-system fit, delivery, runtime/performance, operations, maintenance and Human preference. Do not use a weighted 0–100 score or language stereotype.
3. Recommend at most one primary language and two meaningful alternatives with evidence and trade-offs. Resolve language before framework.
4. Recommend a framework only after language is known. Use version-aware official context for material framework-specific claims.
5. Assess domain, workflow, integration, transaction, change, longevity, team/ownership and risk signals. Use triggers and counter-signals, not a summed score.
6. Keep framework, Clean Architecture, DDD, and deployment choices independent. Simple CRUD should remain simple when evidence supports it. Complex domain does not imply microservices.
7. Present material choices together where possible to reduce approval fatigue; wait for Human confirmation before finalizing the profile.

## Contract resolution

Support REST/OpenAPI first. Record authority explicitly:

- `canonical`: approved contract defines intended behavior;
- `descriptive`: contract documents current behavior;
- `proposed`: contract defines a future target;
- `unresolved`: authority is unknown.

Assess contract, source, tests and observed runtime as separate evidence. Existing-project OpenAPI is not automatically canonical. Do not silently normalize drift. Classify the disagreement and ask for a decision when it materially affects implementation. Even a canonical contract does not authorize an unapproved breaking change. Full automated compatibility and conformance engines are deferred.

## Architecture resolution

Assess qualitatively: domain complexity, workflow, integration, data/transaction, change frequency, longevity, team ownership, and risk/compliance. Record triggers and counter-signals with evidence. Choose an appropriate level such as simple, modular, domain-oriented or domain ecosystem; these are not maturity rankings.

Resolve Clean Architecture, tactical/strategic DDD, logical boundaries, and deployment model as separate fields. In particular, `DDD → Microservices` is not a valid automatic inference. In existing projects, preserve observed patterns unless the requirement or an approved change says otherwise.

## Language, framework, and knowledge

Load one of the stable Go, PHP, Python, or .NET language profiles. Keep framework/library conventions separate from language guidance and honor detected project toolchains. For version-sensitive framework behavior, consult official documentation for the selected version only when the evidence gap matters. Record source/version/provenance; do not copy a full framework knowledge base into AIPS. Repeated knowledge gaps may enter Capability Incubation for later review.

## Ownership resolution

Use four categories: `generated`, `scaffolded`, `project_owned`, and `unresolved`. `project_owned` includes handwritten code. Detect generator manifests, commands, headers and CI generation steps where applicable. Unknown paths remain protected. A path cannot appear in more than one category. Phase 1 does not run generators.

## Quality and completion

Build the profile from universal mandatory checks, project-required checks, risk-triggered checks, and advisory checks. Preserve project commands. Record evidence status as `PASS`, `FAIL`, `UNVERIFIED`, or `BLOCKED`, with command/source and result provenance. Add API compatibility, generated drift, security, or deeper verification only when applicable and evidence-backed. Do not require arbitrary coverage percentages.

## Blocking, assembly, and handoff

Assemble `templates/implementation/IMPLEMENTATION_PROFILE.yaml` only after material decisions are resolved. If any `unresolved` item has `blocking: true`, the profile is structurally valid but implementation readiness is `BLOCKED`; continue independent work where safe. Unknown contract authority blocks contract-affecting code. An optional unverified detail may remain unresolved with a reason.

Pass the profile and relevant local references to the existing Backend Engineer and existing skills. The implementer follows TDD and project-native commands, records actual verification evidence, and hands the exact diff to Review. The profile is input evidence, not permission to alter out-of-scope files.

## Structural validation

Run the deterministic validator against a profile; optionally validate its selected language profile in the same invocation:

```bash
python scripts/implementation_profile_validate.py path/to/IMPLEMENTATION_PROFILE.yaml \
  --language-profile references/languages/go/PROFILE.yaml --format json
```

`structural_status` reports `PASS` or `FAIL`; `implementation_status` reports `READY` or `BLOCKED`. Exit codes are 0 for structurally valid and ready, 1 for structural errors, and 2 for a structurally valid but blocked profile. The validator checks allowed states/enums, required sections, decision provenance, profile consistency, normalized repository-relative ownership paths, ownership overlap, unresolved blockers and language profile shape. It does not assess semantic quality or choose a technology.

## Non-goals and phases

Phase 1: Resolution contract, profile template, Go/PHP/Python/.NET profiles, Project Intelligence and planning integration, structural validator, representative conformance, diagrams and Human guidance.

Later: Phase 2 OpenAPI validity/compatibility, implementation conformance, contract testing and evidence provenance automation; Phase 3 deterministic ownership/provenance/drift/quality enforcement integrated into existing gates; Phase 4 justified generator adapters for transport/client boundaries only.

Do not add language-specific Roles, framework Skills/Profiles, code-generator adapters, GraphQL/gRPC/AsyncAPI support, automatic migrations, or automatic framework modernization in Phase 1.
