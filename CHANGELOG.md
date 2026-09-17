# Changelog

## 0.18.0

### Instruction Conflict Resolution Surface

- Add a structured instruction-resolution surface to Turn Context that preserves runtime-native and project-authoritative sources while keeping derived Project Intelligence explicitly non-governing.
- Surface recorded instruction conflicts from Project Overrides / Project Intelligence with registered source pointers, scope, materiality and status instead of silently discarding either source.
- Fail closed for mutating work when an unresolved material instruction conflict is present; read-only work remains soft while exposing the conflict for human/Agent reconciliation.
- Extend Project Overrides and Turn Context templates with the additive conflict-resolution contract.
- Add executable lifecycle evidence for Scenario 064 and promote it from manual to lifecycle.
- Raise conformance baseline to 125 total / 9 manual / 19 deterministic / 45 lifecycle / 52 agent_eval / 116 automated / 0 uncovered (92.8% automated).
- Architecture Diagram Impact: N/A — context-resolution behavior and schema are extended, but runtime topology, Role, Skill, Capability, Approval Gate and Constitution remain unchanged.

## 0.17.1

### Residual Harness Migration Evidence Maturity

- Add executable lifecycle evidence for legacy AIPS installation migration through preflight into the managed Global Harness model.
- Verify the old preflight fast-forwards and re-execs the updated CLI, an installed system refreshes managed Harness content, user-owned instructions survive composition, colliding foreign registrations remain CONFLICT/MANUAL, and a plain repository checkout does not register the Global Harness implicitly.
- Promote Scenario 068 from manual to lifecycle without adding or changing runtime product behavior.
- Keep the remaining manual Scenarios truthful: visual scenarios still require rendered evidence; API performance requires measured benchmark evidence; 028/054/064/082/087 require additional end-to-end product capabilities or conflict/lazy-loading behavior before promotion.
- Raise conformance baseline to 125 total / 10 manual / 19 deterministic / 44 lifecycle / 52 agent_eval / 115 automated / 0 uncovered (92.0% automated).
- Architecture Diagram Impact: N/A — evidence, validation and release metadata only; no runtime topology, Role, Skill, Capability, Approval Gate or Constitution change.

## 0.17.0

### Project / Architecture Lifecycle Evidence Maturity

- Add Agent Eval evidence for brownfield REST change planning, infrastructure cost analysis, Deployment Unit repository strategy, review-learning feedback and evidence-based Project Intelligence discovery.
- Add executable legacy Project Knowledge migration lifecycle evidence that preserves `.ai/knowledge` as migration evidence while new reusable conclusions write to canonical Project Intelligence and authoritative sources remain pointer-over-copy.
- Promote Scenarios 002, 006, 029, 043 and 052 to agent_eval, and Scenario 088 to lifecycle.
- Keep Scenarios 004, 028, 054 and 087 manual because their complete contracts require reproducible performance measurement, full production delivery lifecycle, approval-backed authoritative promotion, or real monorepo lazy-loading evidence respectively.
- Raise conformance baseline to 125 total / 11 manual / 19 deterministic / 43 lifecycle / 52 agent_eval / 114 automated / 0 uncovered (91.2% automated).
- Architecture Diagram Impact: N/A — evidence/conformance and release metadata only; no runtime topology, Role, Skill, Capability, Approval Gate or Constitution change.

## 0.16.9

### Interaction & Context Evidence Maturity

- Add Agent Eval evidence for scoped instruction conflict handling, adaptive bounded subagent/model routing, safe professional defaults, external-context authorization/resume, external-context fallback and Architecture Diagram Impact decisions.
- Promote Scenario 063 to lifecycle using the existing executable normal-chat Harness/Project Intelligence fixture; it verifies general conversation remains EPHEMERAL and does not create `.ai/`, External Project Intelligence or Change Impact state.
- Keep Scenarios 064, 068 and 082 manual: current executable evidence covers adjacent source composition, preflight/Harness lifecycle and Project Intelligence refresh behavior, but does not yet exercise each scenario's complete contract end to end.
- Promote Scenarios 008, 010, 036, 037, 038 and 065 to agent_eval, and Scenario 063 to lifecycle.
- Raise conformance baseline to 125 total / 17 manual / 19 deterministic / 42 lifecycle / 47 agent_eval / 108 automated / 0 uncovered (86.4% automated).
- Architecture Diagram Impact: N/A — evidence/conformance metadata only; no runtime topology, Role, Skill, Capability or Approval Gate change.

## 0.16.8

### Product & Visual Evidence Maturity

- Add Agent Eval evidence for Product Creation, design-only Nordic concepts, aspect-level mixed references, reusable Brand System creation and evidence-driven redesign escalation.
- Add deterministic Project Visual Profile freshness evaluation plus lifecycle evidence: unchanged watched visual sources reuse the approved profile, while changed shared tokens/components trigger targeted refresh instead of a blind full rescan.
- Keep Scenarios 021, 022, 039 and 055 manual because complete verification requires real rendered/screenshot evidence that the repository-only harness cannot currently produce.
- Promote Scenarios 001, 003, 023, 024 and 040 to agent_eval, and Scenario 056 to lifecycle.
- Raise conformance baseline to 125 total / 24 manual / 19 deterministic / 41 lifecycle / 41 agent_eval / 101 automated / 0 uncovered (80.8% automated).
- Architecture Diagram Impact: N/A — no runtime topology, Role, Skill, Capability or Approval Gate change.

## 0.16.7

### Core Planning & Change Assurance Semantic Evidence Maturity

- Add Agent Eval evidence for delivery sequencing from an existing complete plan, adaptive DDD/Clean Architecture use, capability gaps, Documentation Impact, reproducible two-gate Planning Packages, deterministic preprocessing, audience-separated documentation and Core Change impact-derived testing.
- Add scope-expansion evidence that recomputes the Core Change Test Matrix, executes newly applicable checks, reruns affected review and follows applicable reapproval.
- Promote Scenarios 005, 007, 009, 012, 013, 026, 027, 092 and 093 from manual to agent_eval.
- Raise conformance baseline to 125 total / 30 manual / 19 deterministic / 40 lifecycle / 36 agent_eval / 95 automated / 0 uncovered (76.0% automated).
- No runtime behavior, Role, Skill, Capability, Approval Gate or architecture-topology change.

## 0.16.6

### Security & Production Readiness Semantic Evidence Maturity

- Add Agent Eval evidence for proportional security assurance across critical financial boundaries, low-impact frontend work and cosmetic changes inside critical products.
- Add semantic evidence for security planning/review, Release Readiness blockers, production verification/recovery, staging N/A for low-risk static products and deployment automation with missing platform access.
- Promote Scenarios 014-016 and 030-034 from manual to agent_eval.
- Raise conformance baseline to 125 total / 39 manual / 19 deterministic / 40 lifecycle / 27 agent_eval / 86 automated / 0 uncovered (68.8% automated).
- No runtime behavior, Role, Skill, Capability, Approval Gate or architecture-topology change.

## 0.16.5

### Quality & Release Semantic Evidence Maturity

- Add Agent Eval evidence for Q2 quality baseline selection and independent quality-dimension adjustment.
- Add semantic evidence for deriving draft quality targets from product scale, failure impact, sensitivity, delivery and operations context without forcing users to invent p95/RTO/RPO.
- Add evidence for LOCAL_COMPLETE before optional Production Enablement when production was not requested.
- Add evidence for explicit production requests: plan production concerns from the start, still verify LOCAL_COMPLETE, then continue without a redundant deploy question and require Release Readiness.
- Add provider-neutral observability evidence before vendor selection.
- Add high-value audit logging evidence for balance/points/refund/role actions with stronger access/integrity/retention/redaction requirements.
- Promote Scenarios 045-050 from manual to agent_eval.
- Raise conformance baseline to 125 total / 47 manual / 19 deterministic / 40 lifecycle / 19 agent_eval / 78 automated / 0 uncovered (62.4% automated).
- No runtime behavior, Role, Skill, Capability, Approval Gate or architecture-topology change.

## 0.16.4

### Governance & Security Semantic Evidence Maturity

- Add provider-neutral Agent Eval evidence for Git Publish Approval, Change Impact before mutation, secure runtime credential acquisition, active secret-exposure release blocking and private-config rejection during Skill admission.
- Reconcile Scenario 084 from malformed legacy Markdown into the current pre-mutation impact + post-diff reconciliation contract.
- Bind all five new observable GPT-5.6 Sol results to exact Case SHA-256 fingerprints and deterministic rubrics.
- Keep Git publication command guards and secret scanner evidence as lower-layer deterministic controls while using Agent Eval for the higher-level semantic decisions.
- Promote Scenarios 018, 084, 089, 091 and 095 from manual to agent_eval.
- Raise conformance baseline to 125 total / 53 manual / 19 deterministic / 40 lifecycle / 13 agent_eval / 72 automated / 0 uncovered (57.6% automated).
- No runtime behavior, Role, Skill, Capability, Approval Gate or architecture-topology change.

## 0.16.3

### Intelligence Context Evidence Maturity

- Add focused executable evidence for Project Intelligence source-pointer and normal-chat context behavior.
- Verify AGENTS, CLAUDE, GEMINI and official project docs remain authoritative pointers with `content_duplicated: false`.
- Verify runtime-aware deduplication: sources already native to the current Runtime are not reinjected as project context, while non-native authoritative sources remain targeted-load pointers.
- Verify deterministic bootstrap does not copy authoritative instruction/doc content into derived Intelligence topics.
- Verify normal general-knowledge turns may receive compact Harness context without creating project `.ai/`, External Project Intelligence or Change Impact state.
- Reconcile Scenarios 076 and 086 into explicit current contracts and promote them from manual to lifecycle coverage.
- Keep Scenarios 064, 082, 084, 087 and 088 manual because their full semantic/behavioral contracts are not yet deterministically enforced; no partial-coverage promotion is claimed.
- Raise conformance baseline to 125 total / 58 manual / 19 deterministic / 40 lifecycle / 8 agent_eval / 67 automated / 0 uncovered (53.6% automated).
- No runtime behavior, Role, Skill, Capability, Approval Gate or architecture-topology change.

## 0.16.2

### Install / Preflight Evidence Maturity

- Add isolated full CLI lifecycle evidence using temporary AIPS Git repositories, local bare remotes, temporary product repositories and isolated HOME/config/bin paths.
- Verify Update Preflight requires clean `main`, uses fast-forward-only updates, blocks divergent history and requires explicit `--allow-major` for major upgrades.
- Verify updated CLI re-entry after a successful system fast-forward.
- Verify EPHEMERAL projects are not auto-attached and target product repositories are never automatically pulled.
- Verify ATTACHED project `.ai/SYSTEM.yaml` refreshes exact AIPS version/commit provenance after update.
- Verify attach/status/detach/restore/uninstall lifecycle and preservation of product source, project workspace, External Intelligence, system repository and venv by default.
- Verify explicit cache/venv removal remains opt-in.
- Verify regular-file and foreign-symlink CLI collisions are non-destructive while the exact AIPS-owned symlink can be safely reused.
- Ignore Python `__pycache__/` and `*.py[cod]` runtime artifacts so normal AIPS Python execution cannot make the System repository fail its own clean-worktree preflight gate.
- Promote Scenarios 011, 044 and 069 from manual to lifecycle coverage.
- Raise conformance baseline to 125 total / 60 manual / 19 deterministic / 38 lifecycle / 8 agent_eval / 65 automated / 0 uncovered (52.0% automated).
- No Role, Skill, Capability, Approval Gate or architecture-topology change; architecture diagrams are N/A.

## 0.16.1

### Focused Harness Evidence Maturity

- Add focused executable Harness runtime lifecycle evidence using isolated fake Codex, Claude and Gemini runtimes.
- Verify truthful runtime installation status, Context Capability and Governance Enforcement state.
- Fix Harness Resolution to expose `runtime.governance_enforcement` separately from context `capability`, aligning runtime output with the existing Adapter Contract.
- Verify Gemini uses the official namespaced extension mechanism with BeforeAgent Turn Context and does not overwrite user GEMINI.md/settings.
- Verify projects without .ai remain EPHEMERAL during Harness resolution and are not auto-attached.
- Verify Gemini uninstall targets only aips-global-harness.
- Verify failed AIPS-owned Gemini unregister preserves ownership state for safe retry and succeeds after the runtime issue is resolved.
- Reconcile malformed Scenario 072 Markdown into the current Gemini BeforeAgent contract.
- Promote Scenarios 057, 061, 066, 067, 072 and 073 from manual to lifecycle coverage.
- Raise conformance baseline to 125 total / 63 manual / 19 deterministic / 35 lifecycle / 8 agent_eval / 62 automated / 0 uncovered (49.6% automated).
- No runtime, Role, Skill, Capability, Approval Gate or architecture behavior change.

## 0.16.0

### Provider-neutral Agent Eval Conformance

- Add provider-neutral Agent Eval cases and recorded observable results for semantic behavior that cannot be truthfully reduced to deterministic repository checks.
- Add deterministic Case SHA-256 fingerprint binding so changed eval contracts make previous recorded results stale.
- Add structured rubric scoring for equals, contains, excludes, set equality and non-empty observable fields.
- Reject private reasoning / chain-of-thought fields and high-confidence secret-like values in recorded Agent Eval results.
- Keep model execution separate from CI scoring; AIPS core requires no provider SDK and does not claim CI generated a model response.
- Add `aips conformance agent-eval check|report`.
- Promote Scenarios 017, 019, 020, 025, 035, 041, 042 and 094 from manual to agent_eval using recorded GPT-5.6 Sol observable results from the maintainer implementation session.
- Add Scenarios 121-125 for Agent Eval fingerprint, result binding, deterministic rubric, privacy/provider neutrality and lifecycle behavior.
- Raise conformance baseline to 125 total / 69 manual / 19 deterministic / 29 lifecycle / 8 agent_eval / 56 automated / 0 uncovered (44.8% automated).
- No new Role, Skill, Capability or Approval Gate.

## 0.15.1

### Validation Architecture Cleanup

- Refactor the stable `tests/validate_repository.py` entrypoint into a small aggregator over subsystem validation modules.
- Preserve existing validation semantics while separating static contracts, runtime lifecycle, governance/resume, conformance/isolation and shell syntax checks.
- Keep focused one-to-one Scenario evidence under `tests/evidence/`.
- Reorganize maintenance consistency guidance by subsystem instead of accumulating version-number sections.
- Upgrade checkout to v7.0.1 and setup-python to v7.0.0 using immutable full commit SHAs, resolving the runner Node 20 deprecation warning.
- Raise the PyYAML dependency floor to 6.0.3.
- Keep validator policy focused on immutable SHA pinning rather than freezing a specific action version.

## 0.15.0

### Canonical Project Identity and Resume Integrity

- Add one canonical repository/workspace identity contract shared by Project Intelligence, Run State and Execution Isolation.
- Separate repository_id (lineage / repository-wide coordination) from workspace_id (active worktree state) while retaining project_id as a compatibility alias.
- Add `aips identity` for deterministic identity and workspace-fingerprint diagnostics.
- Move EPHEMERAL Run State to the canonical workspace namespace with lazy migration of legacy absolute-path-hash runs.
- Upgrade run checkpoints to version 2 with repository/workspace identity, branch, dirty fingerprint and workspace fingerprint.
- Mark resume STALE when uncommitted product workspace state changes even if Git HEAD is unchanged.
- Exclude AIPS-owned `.ai/` state from workspace fingerprints so checkpoints do not stale themselves.
- Coordinate Execution Isolation writers by repository_id + Change Boundary across Git worktrees and discover verifiable legacy ownership records.
- Keep Project Intelligence on the canonical workspace namespace with compatibility migration when required.
- Add Scenarios 116-120 and executable cross-worktree / resume-integrity lifecycle evidence.
- Raise conformance baseline to 120 total / 77 manual / 43 automated / 0 uncovered.

## 0.14.2

### Governance and Public Repository Hardening

- Normalize protected Git/GitHub publication command detection across executable paths, Git/GH global options, common environment/shell wrappers and compound protected commands.
- Keep approval semantics unchanged while requiring every detected protected publication operation in a compound command to be approved.
- Add focused governance command-normalization evidence to Scenario 099.
- Harden GitHub Actions with explicit read-only contents permission and immutable full-SHA action references.
- Add Dependabot coverage for Python and GitHub Actions dependencies.
- Add SECURITY.md and link it from the Human entry documentation.
- Reconcile Architecture Overview to describe current system state rather than historical version snapshots.
- Align PATCH versioning policy with backward-compatible bug fixes and hardening.
- License selection remains an explicit maintainer decision and is not changed by this release.

## 0.14.1

### Legacy Scenario Reconciliation

- Audit legacy Scenarios 001-095 against the current canonical System, Orchestration, Harness and Project Intelligence contracts.
- Reconcile stale preflight, Project Knowledge and runtime-instruction assumptions without changing Scenario IDs or paths.
- Align legacy Project Knowledge scenarios to Project Intelligence + SOURCE_REGISTRY while preserving `.ai/knowledge/` only for migration compatibility.
- Align Codex/Claude scenarios to managed composition, ownership-safe uninstall and separate context/enforcement capability truth.
- Add focused direct evidence for adapter composition, Project Intelligence lifecycle/freshness/migration and secret redaction.
- Promote only directly exercised legacy Scenarios from manual to deterministic/lifecycle coverage.
- Update conservative conformance baseline to 115 total / 77 manual / 38 automated / 0 uncovered (33.0% automated).
- No runtime behavior, Constitution, Role, Skill, Capability registry or Approval Gate change; architecture diagrams are N/A.

## 0.14.0

### Execution Isolation

- Add explicit `shared | worktree | sandbox` isolation to the existing Execution Profile without introducing a new Role, Skill or approval gate.
- Add real AIPS-owned Git worktree lifecycle with external ownership records and one ACTIVE writer per Change Boundary.
- Block cleanup of dirty worktrees, remove only AIPS-owned managed paths and preserve managed branches after cleanup.
- Report sandbox capability truthfully: without a verified provider, sandbox is UNSUPPORTED/BLOCKED and a temporary directory is never presented as a sandbox.
- Add `aips isolation resolve|create|status|remove`, Workspace Manifest isolation state and scenarios 111-115.
- Raise conservative Scenario Conformance baseline to 115 total / 95 manual / 20 automated / 0 uncovered.
- Update Agent/Human architecture contracts and affected system/lifecycle diagrams.

## 0.13.0

### Harness Conformance

- Add a machine-readable Scenario Conformance Registry mapping every acceptance scenario to coverage type and evidence.
- Distinguish deterministic, lifecycle, agent-eval, manual and uncovered coverage instead of treating scenario count as proof of conformance.
- Add deterministic conformance check/report tooling and `aips conformance check|report`.
- Conservatively classify legacy scenarios without explicit one-to-one executable evidence as manual rather than overstating automation.
- Add scenarios 106-110 and CI checks for complete/unique registry coverage, reporting and missing-evidence failure.
- Constitution, Roles, Skills, Capabilities and Approval Gates remain unchanged.


## 0.12.0

### Observable + Resumable Harness

- Extend existing workspace state with a durable workflow checkpoint contract instead of introducing a new workflow framework.
- Add deterministic run checkpoint/event/resume helpers for ATTACHED and EPHEMERAL project modes.
- Add append-only structured `EVENTS.jsonl` evidence that excludes prompts, chain-of-thought and secret values by contract.
- Bind checkpoints to project revision and return STALE on revision drift so resume cannot silently reuse obsolete evidence.
- Add `aips run checkpoint|event|resume|status` routing and scenarios 101-105 with lifecycle validation.
- Constitution, Roles, Skills, Capabilities and Approval Gates remain unchanged.


## 0.11.0

### Enforceable Governance

- Add machine-readable Approval Records with canonical SHA-256 proposal/scope fingerprints and stale-approval detection.
- Separate Runtime context capability from Governance Enforcement capability: ADVISORY / TOOL_GUARDED / ENFORCED / UNSUPPORTED.
- Add deterministic Git-publication guard primitives for native pre-tool integrations while keeping unsupported runtimes advisory.
- Add structured Turn Context explanation metadata without persisting chain-of-thought.
- Add backward-compatible workspace governance state and scenarios 096-100.
- Constitution, Roles, Skills, Capabilities and Approval Gate count remain unchanged.


## 0.10.0

### Self-Improvement Decision Quality

- Separate User Problem, Proposed Solution and Recommended AIPS Solution so a requested mechanism is evaluated rather than accepted as system architecture by default.
- Require evidence-based checks for existing coverage, reuse/extension candidates and lower-layer alternatives before introducing new abstractions.
- Expand System Improvement Review coverage for context/token cost, security/reliability, backward compatibility, scenarios/tests, Human/Agent docs, Architecture Diagram Impact and semantic Constitution impact.

### Additional Optimization Scope Integrity

- Add Additional Optimization Confirmation for improvements discovered beyond the currently approved request.
- Classify material optimization candidates as NOW / LATER / REJECT and disclose benefit plus scope impact.
- Require explicit Human confirmation before a NOW candidate may enter implementation scope; deferred candidates must not be implemented opportunistically.
- Require scope re-approval when an approved optimization materially expands the Change Boundary.

### Deterministic Regression Protection

- Strengthen Scenario 019 for Problem/Solution separation, reuse-first evaluation and additional-optimization scope control.
- Extend repository validation to enforce the Self-Improvement protocol, review-template and Scenario 019 contracts deterministically.

### Compatibility / Governance

- Backward-compatible orchestration change; no project migration required.
- Constitution unchanged.
- No new Role, Skill, Capability or Approval Gate.

## 0.9.0

### Turn-Aware Global Harness

- Upgrade Global Harness from session/bootstrap-oriented behavior to turn-aware context resolution.
- Keep one Harness contract while using runtime-native integration: Codex CONTEXT_ALWAYS, Claude Code UserPromptSubmit when verifiable, and Gemini CLI BeforeAgent.
- Compose AIPS through reversible managed instruction blocks/hooks/extensions without replacing user-owned Agent instructions or Skills.
- Separate integration status from runtime capability truth: TURN_NATIVE / CONTEXT_ALWAYS / SESSION_ONLY / MANUAL / UNSUPPORTED.

### Project Intelligence

- Replace Project Knowledge as the canonical reusable brownfield understanding layer while preserving legacy knowledge as migration evidence.
- Add PROJECT_INTELLIGENCE, SOURCE_REGISTRY, IMPACT_GRAPH and PROJECT_OVERRIDES contracts.
- Add read-only breadth-first discovery followed by evidence-based semantic enrichment; inventory alone remains PARTIAL until finalize reaches READY.
- Add runtime-aware source deduplication, branch/worktree/dirty-path freshness, one-writer atomic updates and targeted refresh.
- Add deterministic self-contained Project Intelligence Review HTML with secret redaction.
- Add External Project Intelligence Cache so EPHEMERAL projects can reuse understanding without creating project-local .ai state.
- Add validated External ↔ Local Intelligence migration across attach/detach.

### Existing-project Change Safety

- Add Change Impact Guard and per-change impact artifacts covering inputs, outputs, data, events, consumers, security boundaries, invariants and compatibility.
- Preserve valid project-native conventions while refusing to propagate unsafe or demonstrably broken legacy patterns.
- Reconcile actual diff against declared Change Impact and refresh only affected reusable Intelligence.

### Secret / Credential Safety

- Add Secret Handling protocol for secure runtime acquisition through workload identity, secret managers, CI stores, OS/runtime credential stores or environment injection.
- Prohibit real credentials in source, prompts, Project Intelligence, generated HTML, logs, fixtures, snapshots and review artifacts.
- Add deterministic high-confidence secret leakage checker with redacted path/line/detector/fingerprint evidence; detected values are never echoed.
- Add exposure containment/rotation guidance and release blocking for unresolved active production or SAL 3–4 credential exposure.

### Core Change Testing

- Add Impact-derived Core Change Testing contract and machine-readable test matrix.
- Require applicable evidence for every materially affected Change Boundary, with concrete N/A reasons for non-applicable checks.
- Recompute required tests when implementation scope expands and block completion/release on failing or missing required evidence.

### Skill Admission Governance

- Strengthen Capability Incubation with a New Skill admission contract.
- Require reuse-first search, narrow responsibility, triggers/non-triggers, inputs/outputs/boundaries, context/model cost, scenario evidence, unique ID/path and private-config checks.
- Keep project-specific conventions in Project Intelligence and one-off automation in project/run tooling instead of proliferating system Skills.

### Documentation / Architecture / Regression

- Refresh Human and Agent documentation for Turn Harness, Project Intelligence, secret handling, strict core-change testing and safe uninstall/cache behavior.
- Add Project Intelligence architecture diagram and update system/harness/lifecycle diagrams; Product Delivery diagram remains N/A because its lifecycle is unchanged.
- Extend acceptance scenarios through Scenario 095 and executable validator coverage for managed composition, Intelligence lifecycle/freshness, secret leakage, attach/detach migration, core test selection and Skill admission.
- Constitution unchanged; no new Role, Skill or approval Gate.

## 0.8.0

### Global Agent Harness

- Add a cross-Agent Global Harness with a minimal bootstrap and lazy AIPS orchestration.
- Add Runtime Adapter contracts and built-in integrations for Codex CLI, Claude Code and Gemini CLI plus a Generic Manual fallback.
- Use AUTOMATIC / MANUAL / NOT_DETECTED / CONFLICT / ERROR machine-specific coverage states.
- Preserve runtime-native/project instructions instead of replacing them with one global override.

### Non-invasive Installation and Ownership

- Add Harness Ownership Manifest and per-adapter state.
- Never overwrite existing user AGENTS/CLAUDE/GEMINI instruction files to gain automatic coverage.
- Record AIPS-owned runtime resources and remove only owned/unchanged resources.
- Preserve modified AIPS-created bootstrap files rather than deleting possible user content.
- Preserve ownership state when a runtime registration cannot be safely removed, enabling a later uninstall retry.
- Prevent destructive ~/.local/bin/aips name collisions.

### Ephemeral and Attached Project Modes

- Make EPHEMERAL the default for projects without .ai/.
- Stop preflight from implicitly attaching projects or creating persistent AIPS state.
- Keep ATTACHED persistence opt-in through explicit aips attach.
- Add deterministic `aips harness resolve` output for runtime, project root, instructions, Knowledge and State pointers.

### Harness Lifecycle CLI

- Add `aips harness install`, `uninstall`, `status`, `doctor` and `resolve`.
- Make `aips install` enable the Global Harness and `aips uninstall` remove AIPS-owned integrations first.
- Safely refresh/migrate the Harness after installed-system preflight updates.
- Document the v0.7 → v0.8 upgrade path.

### Architecture Diagram Integrity

- Add mandatory Architecture Diagram Impact Check to the existing Documentation Impact Gate for Large/Core changes.
- Update Maintainer Mermaid flows for Global Harness, runtime/project instruction composition, EPHEMERAL/ATTACHED lifecycle and current product delivery.
- Add a Global Harness SVG and refresh system, product-delivery and installation lifecycle SVGs.
- Require affected diagrams to be updated or explicitly marked N/A with a reason.

### Documentation and Regression Coverage

- Add Traditional Chinese Harness/installation/uninstallation guidance and explain exactly what AIPS preserves.
- Add scenarios through Scenario 069 for automatic/manual adapters, ownership-safe uninstall, EPHEMERAL behavior, instruction composition, diagram impact, upgrade migration and CLI collision safety.
- Extend existing orchestration only; no new Role, Skill or approval Gate.

## 0.7.0

### Quality-aware Product Planning

- Add Q1 Lightweight / Q2 Standard / Q3 Critical quality baselines.
- Evaluate Performance, Security, Usability, Reliability, Maintainability, Resource/Cost and Delivery Time for complete products.
- Convert vague quality expectations into measurable targets/budgets, verification methods and evidence.
- Use range + confidence for resource/cost/time estimates and refine after architecture decisions.
- Keep observability requirements provider-neutral until the production environment is known.

### Local Complete and Production Enablement

- Split complete-product delivery into LOCAL_COMPLETE and PRODUCTION_VERIFIED milestones.
- Default complete-product requests to a verified locally runnable system.
- Ask whether to continue to Production only after LOCAL_COMPLETE when production was not explicitly requested.
- Carry explicit production requests through Production Enablement without a redundant second prompt.
- Plan structured logs/health/metrics/traces/audit instrumentation before deployment and choose concrete ELK/Loki/Prometheus/Grafana/OpenTelemetry/managed services later.

### Persistent Project Knowledge

- Add a Project Knowledge layer under .ai/knowledge for stable, expensive-to-rediscover information.
- Prefer pointers to AGENTS/ADR/contracts/official docs instead of duplicating authoritative content.
- Distinguish FACT / INTERPRETATION / OBSERVED_CONVENTION and AUTHORITATIVE / DISCOVERED / APPROVED / STALE states.
- Add evidence/confidence, watched paths/signals, targeted refresh and optional promotion to authoritative project rules.
- Keep cached security knowledge below active security review requirements.

### Visual Consistency Repair

- Add V1 Focused Repair and V2 Product Consistency Sweep.
- Route whole-project vague visual cleanup requests to V2.
- Add representative routes, component inventory, UI consistency baseline and visual outlier detection.
- Require variant/exception classification before normalizing differences.
- Map material findings to DOM/component/computed-style/token root causes where tooling permits.
- Add state geometry stability and rendered before/after verification.
- Persist reusable visual knowledge in PROJECT_VISUAL_PROFILE.yaml.

### Regression Coverage

- Add scenarios through Scenario 056 for quality planning, local/production milestones, observability, project knowledge and V2 visual consistency.
- Extend repository validation to new Quality/Knowledge/Visual templates and workspace contracts.
- Extend existing roles/skills only; no new Role, Skill or Gate.


## 0.6.0

### Progressive Requirement Clarification

- Add READY / NEEDS_CLARIFICATION / BLOCKED requirement readiness.
- Stop broad implementation when material ambiguity remains.
- Prefer safe professional defaults for non-material details.
- Ask only the smallest useful blocking questions with concrete options/recommendations.

### External Context Resolution

- Add connector/MCP-first resolution for user-provided external URLs and references.
- Preserve pending task/source across authorization and resume afterward.
- Fall back to public web or other supported provider paths before asking users to paste/upload content.
- Persist source/retrieval provenance.

### Visual Implementation Polish

- Add Preserve Before Redesign and Consistency First defaults.
- Add rendered Visual Implementation Audit for alignment, typography, spacing, control geometry, icon baseline, states and responsive behavior.
- Prefer shared token/component fixes over page-specific pixel patches.
- Require screenshot/rendered verification when the UI environment can be run.

### Multi-Perspective Review & Learning

- Add risk-based review panels for large/core/high-risk changes using existing specialist roles.
- Use bounded read-only reviewer scopes and independent reviewer model routing.
- Normalize/deduplicate findings before returning them to the original Author.
- Keep the original Author as the writer; use targeted re-review after fixes.
- Extract run/project/system-capability lessons and require user-approved System Improvement before permanent capability changes.

### Installation & Project Lifecycle

- Add aips attach, detach and status.
- Keep aips init as a backward-compatible attach alias.
- Add reversible detach that archives .ai rather than deleting project AI state.
- Ensure preflight respects detached-workspace safety.
- Add scripts/uninstall.sh as the symmetric uninstall wrapper.
- Expand Traditional Chinese lifecycle documentation with install/attach/preflight/detach/uninstall/reinstall guidance and an SVG lifecycle diagram.

### Regression Coverage

- Add scenarios through Scenario 044 for clarification, connector authorization/fallback, visual polish, multi-review, learning feedback and lifecycle behavior.
- Extend repository validation to new protocols/templates and run attach/status/detach/reattach lifecycle checks.


## 0.5.0

### End-to-End Product Delivery

- Add a complete-product lifecycle from user intent/materials through guided planning, implementation, local verification, staging, Release Readiness, production promotion and post-deploy verification.
- Add root `PRODUCT.yaml` as the compact Product Manifest for Deployment Units, contracts, environments, commands, delivery and observability.
- Define Product Workspace as the discoverable System of Record for specifications, brand, code, tests, infrastructure, deployment and operational artifacts.
- Treat frontend/backend/worker components as independent Deployment Units without forcing separate Git repositories.
- Default to monorepo for coordinated product work; require evidence for multi-repo boundaries.

### Local, Staging and Production

- Add Local Environment, Deployment Plan and Operations Runbook templates.
- Make Local → CI → Staging → Production the default material production flow.
- Allow staging to be N/A for genuinely low-risk/simple products with a recorded reason.
- Define production completion as verified deployment plus applicable health, smoke, logs/metrics and recovery evidence.

### Release Readiness

- Add consolidated Release Readiness protocol and YAML contract for exact release candidates.
- Cover build, test, security, migration/recovery, infrastructure, staging, observability and documentation evidence.
- READY remains technical readiness and never bypasses required human/security approval.
- Apply the existing SAL 4 unresolved High/Critical hard floor without over-blocking lower SAL risk-accepted reviews.
- Material candidate changes invalidate affected readiness evidence.

### Deployment Automation

- Require complete products to create repeatable CI/CD/deployment automation appropriate to the target platform.
- Execute deployment automation when platform access and approval are available.
- Persist runnable automation and mark delivery BLOCKED when required platform access/credentials are unavailable.
- Keep production secrets outside source control.

### Deterministic Delivery Checks

- Add `scripts/check_release_readiness.py` to evaluate structured Release Readiness data before AI reasoning.
- Add READY/BLOCKED/SAL3-risk fixtures and repository validation coverage.

### Reuse and Documentation

- Extend existing Delivery Planner, Cloud Architect, SRE and `delivery-planning` Skill rather than adding new delivery/DevOps Roles.
- Update Product Creation, Planning Package, workspace state, Traditional Chinese Human Guide and architecture diagrams.
- Add product-delivery architecture SVG and scenarios through Scenario 034.


## 0.4.0

### Creative Intelligence

- Add reference-grounded Creative Direction for websites, UI, banners, hero visuals, social assets, presentations, product pages and campaigns.
- Add progressive Creative Calibration for vague visual language and aspect-level reference mixing.
- Add reusable Style Profiles as reference data rather than style-specific Skills/Roles.
- Add Visual Quality Review that adapts checks to the artifact type.
- Prioritize user-owned assets, accepted Brand/Visual Systems and explicit user intent before generic design inference.

### Brand System

- Add reusable Brand Foundation & Brand System protocol.
- Add compact BRAND_PROFILE.yaml for agent quick-load plus deeper human-readable brand guidance.
- Add Brand Foundation, Identity, Logo, Verbal, Application and Governance templates.
- Support temporary campaign overrides without silently mutating permanent brand policy.
- Reuse Product Manager/Product Designer instead of creating new Brand roles by default.

### Capability simplicity

- Add reuse-first Capability Incubation before creating or expanding Roles, Capabilities or Skills.
- Require comparison of existing responsibility, triggers, input/output, authority and review obligations.
- Prefer Reuse → Extend → New Skill → New Capability → New Role.
- Add regression checks against unknown Work Mode default roles and duplicate YAML keys.

### Deterministic Automation

- Add Deterministic Automation First for repeatable rule-based parsing, filtering, counting, validation and transformation.
- Prefer existing tools or small Shell/Python helpers before spending model reasoning/context on raw data.
- Standardize structured JSON/YAML summaries with raw evidence referenced separately.
- Define helper lifecycle: run-local → project reusable → system reusable only after demonstrated reuse.
- Add Minimum Sufficient Reasoning as a core principle.

### Human and Agent documentation

- Split Human and Agent documentation entry surfaces.
- Human-facing docs are now Traditional Chinese with English annotations for specialized terms.
- Add 5-minute Getting Started and Documentation Map.
- Keep Agent bootloader concise and protocol-driven.
- Add a source-controlled SVG architecture overview for new users.
- Extend Documentation Impact Gate to check both Human and Agent audiences.

### Regression coverage

- Add scenarios for vague visual requests, user-owned creative assets, mixed references, reusable Brand Systems, duplicate-role prevention, deterministic automation and documentation audience separation.
- Expand repository validation for creative/brand/style/automation artifacts and documentation integrity.

## 0.3.0

### Security assurance

- Add Risk-Proportional Security Assurance with Security Assurance Levels (SAL) 0–4.
- Separate Product Baseline SAL from Change Security Impact so low-risk changes in critical products remain lightweight.
- Add critical risk floors so financial/stored-value integrity cannot be averaged down.
- Add independent Security Engineer review and release gating for high/critical affected boundaries.
- Add threat-modeling, authorization-security, business-logic-abuse, financial-integrity and security-testing skills.
- Add security planning/review templates and Risk Profile schema.
- Treat payments, refunds, stored value, balances, redeemable points/credits/vouchers/coupons and similar value flows as security boundaries.
- Keep Security Assurance separate from Reliability Impact and Model Tier.

### System self-improvement governance

- Add a protected Constitution containing only fundamental human-authority, truth, safety, stop-the-line, scope-integrity and high-risk approval principles.
- Add System Self-Improvement Review for every proposed optimization to this AI Product System.
- Require analysis of appropriateness, overlap, simpler alternatives, additional optimization, compatibility, scenario/doc impact and Constitution semantics before implementation.
- Add Constitutional Change Gate with affected-Article/risk analysis and a second explicit approval.
- Prefer Skill/Template → Workflow/Work Mode → System/Orchestration → Governance → Constitution.

### Change and Git governance

- Add Core Change Approval Gate for semantically large/core changes before implementation.
- Add Git Publish Approval Gate with complete changed-file list, feature summary, validation evidence, atomic commit plan and target before remote publication.
- Group commits by logical capability/reviewability/revertability rather than by file.
- Require re-approval when approved implementation scope or publication plan materially drifts.
- Add security, core-change, Git-publish, self-improvement and constitutional regression scenarios.

## 0.2.0

- Add `aips` CLI with install, uninstall, init, update, preflight, doctor, validate and version commands.
- Add safe Update Preflight using a clean-worktree check, `git pull --ff-only`, divergence blocking and explicit major-version approval.
- Record exact AI Product System version and commit in each initialized project at `.ai/SYSTEM.yaml`.
- Add Documentation Impact Gate and source-controlled Mermaid architecture diagrams.
- Add GitHub Actions validation for repository integrity.
- Add Reproducible Planning Package for authoritative product/project planning.
- Add workspace-first persistence rule for primary planning tasks.
- Add two-stage approval: Planning Package Approval, then Implementation Readiness Approval.
- Add complete planning templates covering product, UX, key visual/visual system, architecture, API, implementation readiness and decisions/assumptions.
- Add installation/lifecycle and planning-gate regression scenarios.

## 0.1.0

- Initial governed AI Product System baseline.
