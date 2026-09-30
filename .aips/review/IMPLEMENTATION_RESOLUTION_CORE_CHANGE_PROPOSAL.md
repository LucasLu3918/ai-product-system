# Implementation Resolution Core Change Proposal

## Purpose

Add an evidence-driven resolution layer between requirements/project understanding and code implementation. It will prepare a bounded, provenance-bearing Implementation Profile for REST/OpenAPI work in existing or new projects, then route that profile to existing implementation roles and skills.

## Problem and recommendation

API documentation alone does not tell an agent which contract is authoritative, how an existing repository expects code to be structured, which files are generated, or which project checks must pass. New projects also need a guided, human-confirmed way to select technology and architecture. Extend existing orchestration, Project Intelligence, REST API guidance, quality planning, and conformance; do not add a parallel scanner or specialist role hierarchy.

## Goals

- Support REST/OpenAPI contracts first, with explicit `canonical`, `descriptive`, `proposed`, and `unresolved` authority.
- Resolve existing-project work from repository evidence and local examples; guide new-project choices with trade-offs and Human confirmation.
- Produce an auditable Implementation Profile with evidence, resolution states, ownership, quality requirements, and blocking unknowns.
- Add stable Go, PHP, Python, and .NET language profiles and a deterministic structural validator.
- Cover the highest-risk decision boundaries with representative conformance scenarios and update the architecture and Human documentation.

## Change boundary

Add `orchestration/IMPLEMENTATION_RESOLUTION.md`, an Implementation Profile template, four language profiles, and `scripts/implementation_profile_validate.py`. Extend Project Intelligence, requirement clarification, external context resolution, planning, quality planning, and the REST API skill. Add deterministic contract tests, one lifecycle evidence suite, Scenario 193 and registry/documentation entries, architecture diagrams, Human guidance, a Core Change Test Matrix, review artifacts, and release notes/version metadata.

## Non-goals

No language-specific Engineer Roles, Framework Advisor/API Generator Roles, idiomatic-implementation or framework Skills, Framework Profiles, generator adapters, GraphQL/gRPC/AsyncAPI implementation, automatic architecture migration, framework modernization, full contract test engine, or breaking-change engine. Phase 2–4 work remains deferred.

## Architecture, contract, and data impact

The new resolution step sits between Project Intelligence/Planning and existing implementation roles. It creates a YAML profile as a planning artifact; it does not alter AIPS runtime APIs, persisted product data, generated application code, or deployment topology. The architecture diagram is affected because a new formal stage and profile are added.

## Authority and safety

Human decisions remain final for new-project language/framework/architecture selection and contract-affecting changes. Existing explicit project rules outrank generic recommendations unless a higher authority, safety rule, approved contract, or hard compatibility constraint applies. Unknown ownership is protected. Conflicting evidence remains visible. No verification is not PASS. The validator checks structure only and cannot approve semantic choices.

## Compatibility and migration

Additive guidance and optional profile templates preserve existing projects. Existing repositories do not need migration or `.ai/` attachment. Existing project conventions remain the default. Phase 1 does not run code generators or rewrite project files.

## Validation and documentation

Run focused deterministic/lifecycle checks, full repository validation, Scenario Conformance, documentation sync/placement, YAML/Markdown/Python checks, publication preview, strict candidate secret scan, and the Core Change Integration Gate when supported. Update Agent protocols, Human User Guide, Technology Guide, Architecture Overview, architecture diagram, Conformance inventory, and changelog in the same candidate.

## Risks and mitigations

- **Over-inference from sparse evidence:** preserve provenance and explicit `not_detected` / `unresolved` / `conflicting` states; require local evidence and Human decisions.
- **Architecture inflation:** use qualitative triggers and counter-signals; keep logical and deployment architecture separate.
- **Ownership overwrite:** unknown files are protected and ownership overlaps fail structural validation.
- **Scope creep:** defer framework-specific knowledge and generation; reuse existing roles, skills, gates, and project intelligence.
- **Stale project state:** refresh current project evidence before implementation and bind Change Impact to the exact final diff.

## Rollback

Revert this additive change set. No migration or generated-project changes need reversal. Existing projects continue using their prior orchestration when the resolution protocol is absent.

## Approval and implementation order

Implementation scope was explicitly authorized by the user request on 2026-09-30: “請幫我依照建議實作所有事項，本地驗證完後需完成遠端pr合至main”. Implement in dependency order: review/impact, resolution contract, profile/schema, language profiles, Project Intelligence and planning integration, validator, conformance, diagrams and Human docs, full validation, review, then publication readiness.

Constitution impact: **NO expected**. New Role/Skill/Capability/Governance Gate: **NONE**.
