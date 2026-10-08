# Implementation Resolution

Canonical REST API Skill descriptions are portable discovery metadata used by OpenCode projections. The described implementation workflow still resolves the existing project-native contract and verification requirements.

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

Assess contract, source, tests and observed runtime as separate evidence. Existing-project OpenAPI is not automatically canonical. Do not silently normalize drift. Classify the disagreement and ask for a decision when it materially affects implementation. Even a canonical contract does not authorize an unapproved breaking change.

### OpenAPI validation and compatibility

For REST/OpenAPI work, use `scripts/openapi_contracts.py` when specification evidence affects the change. It supports OpenAPI 3.0, 3.1 and 3.2 through the optional pinned dependencies in `requirements-openapi.txt`; validation is offline, rejects remote references, and treats only an explicitly canonical baseline as eligible for compatibility comparison.

```bash
python scripts/openapi_contracts.py validate api/openapi.yaml --repo-root . --output /tmp/openapi-validation.json
python scripts/openapi_contracts.py compare contracts/approved/openapi.yaml api/openapi.yaml \
  --baseline-authority canonical --repo-root . --output /tmp/openapi-compatibility.json
python scripts/openapi_contracts.py verify-evidence /tmp/openapi-validation.json --repo-root .
```

Only internal references and repository-local file references contained within the repository root are accepted. Network references, path traversal, missing files, unsupported versions, invalid specs and missing validator dependencies fail closed; validation never fetches a URL.

Compatibility comparison requires an explicitly selected baseline whose authority is `canonical`. It reports `BREAKING`, `NON_BREAKING`, `NO_CHANGE`, `UNKNOWN` or `BLOCKED`. Operation/response removal, required parameter addition and operation ID change are breaking. Component/schema, security, path-level parameter and other unclassified behavior changes remain `UNKNOWN`; the classifier is conservative and does not claim complete consumer semantics. A breaking result never approves a contract change.

### Contract-test and implementation-conformance evidence

Run the project's documented contract/conformance command with argv JSON and a JUnit XML report. Do not pass a shell command string. The test command receives the desired report location in `AIPS_JUNIT_XML`.

```bash
python scripts/openapi_contracts.py run-contract-tests api/openapi.yaml --repo-root . \
  --command '["go","test","./...","-json"]' --junit build/contract-tests.xml \
  --output /tmp/openapi-contract-evidence.json
python scripts/openapi_contracts.py verify-evidence /tmp/openapi-contract-evidence.json --repo-root .
```

For `PASS`, the command must exit 0, JUnit must contain at least one non-skipped test, and every OpenAPI operation ID must appear in a JUnit test name/class. Failed commands/tests report `FAIL`; timeout, skipped or missing operation coverage reports `UNVERIFIED`; malformed or unavailable evidence reports `BLOCKED`. AIPS records argv/output digests rather than raw command output. The test suite remains project-owned; operation-name matching proves declared coverage evidence, not semantic quality of the assertions.

Evidence binds the spec and JUnit file hashes plus the full Git revision. `verify-evidence` reports `STALE` after any input hash or repository revision change. Re-run evidence on the exact candidate revision. Profile fields link validation, compatibility and conformance reports; a `PASS` without its report and content hash is structurally invalid.

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

`structural_status` reports `PASS` or `FAIL`; `implementation_status` reports `READY` or `BLOCKED`. Exit codes are 0 for structurally valid and ready, 1 for structural errors, and 2 for a structurally valid but blocked profile. The validator checks allowed states/enums, required sections, decision provenance, profile consistency, normalized repository-relative ownership paths, ownership overlap, unresolved blockers, language profile shape and the optional Phase 3 evidence declarations. It does not assess semantic quality or choose a technology. A structural `READY` does not replace the Phase 3 candidate report when enforcement applies.

## Phase 3 deterministic enforcement

The additive `enforcement` section is optional for existing Profiles. Set `mode: report` while establishing coverage, then `mode: enforce` for an approved task scope. Declare repository-relative `scope_paths`, the selected language Profile, generated-file records and project-native argv commands. Changed in-scope paths require explicit ownership evidence; `unresolved` and unlisted paths stay protected. Generated records bind an output hash, input hashes and tool/version, but matching hashes do not prove a generator ran or the generated behavior is correct.

For each applicable `quality.mandatory`, `quality.project_required` and `quality.risk_triggered` entry, declare an `id`, `command_id` and current-run `evidence_report`. A report is bound to the Profile bytes, command argv, command source file and exact Git revision. Command evidence must be ephemeral in the current checkout; committed command reports are rejected. Project commands remain project-owned and their assertions remain subject to review.

Explicit local collection is separate from Gate verification:

```bash
python scripts/implementation_enforcement.py run-command IMPLEMENTATION_PROFILE.yaml \
  --repo-root . --command-id project-check --repeat 2 --execute \
  --output evidence/project-check.json
python scripts/implementation_enforcement.py inspect IMPLEMENTATION_PROFILE.yaml \
  --repo-root . --base <base-sha> --head HEAD --mode enforce \
  --output /tmp/implementation-enforcement.json
```

Use `--repeat 2` for commands declared deterministic. Collection uses argv without a shell, a declared timeout, minimal environment and digest-only bounded output; it does not run automatically in the Gate. The Phase 3 inspector re-verifies selected language identity, Profile fingerprint, generated input/output hashes, required command evidence, and Phase 2 OpenAPI report kind/status/path/hash/revision. `FAIL`, `BLOCKED` and `UNVERIFIED` cannot satisfy enforcement. A report with the same inputs has the same normalized fingerprint; command repeat mismatches remain `UNVERIFIED`.

## Non-goals and phases

Phase 1: Resolution contract, profile template, Go/PHP/Python/.NET profiles, Project Intelligence and planning integration, structural validator, representative conformance, diagrams and Human guidance.

Phase 2: OpenAPI validity and conservative compatibility analysis, project-native contract-test execution, operation coverage and revision/hash-bound evidence reports.

Phase 3: optional, scoped deterministic ownership/provenance/drift/quality enforcement integrated into the existing Gate. Phase 4 remains justified generator adapters for transport/client boundaries only.

## Phase 4 — Explicit OpenAPI client generator adapters

The optional `generation.adapters` contract supports a repository-local OpenAPI client CLI only when the project has a canonical OpenAPI source and current Phase 2 evidence. It pins the executable digest, exact version output, argv, declared tool inputs, output directory and allowlisted output patterns. Existing Profiles remain compatible; generation stays disabled unless both the Profile enables `boundary_only` and the Human explicitly passes `--execute` to `scripts/openapi_generator_adapter.py`.

Default invocation is preview-only and never runs the tool. Local execution stages read-only copies of the specification and tool inputs, invokes argv without a shell in a minimal environment with a bounded timeout, and captures only a digest, byte count and bounded preview in memory. Deterministic adapters run twice and outputs must match. Symlinks, undeclared/oversized files, missing/stale OpenAPI evidence, changed tool inputs and hand-edited or unowned prior output block apply. Existing generated output may be replaced only when Phase 3 ownership and input/output hashes still match. The output directory and updated ownership/provenance records are applied with same-filesystem swaps and rollback.

The adapter is a local subprocess boundary, not an OS sandbox: a malicious or compromised executable may access resources available to the current user. Run only a trusted, repository-pinned tool. The report does not establish semantic client correctness. CI and the Integration Gate inspect reports and fixture behavior but never execute a project-configured generator. A concrete production generator is selected only after the target project supplies canonical spec, language, supported version and approved toolchain evidence.

Phase 5 may opt in to `enforcement.generator_reports` with an adapter ID and an untracked report path. The Phase 3 inspector verifies a completed Phase 4 run against the current Profile, canonical spec, pinned executable/version/argv, input hashes, exact output set, generation records and candidate history. Inspection never runs the generator. The shared Widgets pilot demonstrates this evidence chain and exercises a generated client against a local service; each actual product must retain its own contract and semantic acceptance tests.

Do not add language-specific Roles, framework Skills/Profiles, GraphQL/gRPC/AsyncAPI support, automatic migrations, or automatic framework modernization as part of Phases 1–4.

The REST Skill loads this protocol on demand for OpenAPI evidence, Phase 3 ownership and Phase 4 generation. This protocol remains authoritative for report binding, provenance and explicit Human execution; Skill condensation does not remove these requirements.
