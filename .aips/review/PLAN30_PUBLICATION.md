# Plan30 Publication Improvement — approved Core boundary

Appropriateness: conditionally suitable. Reuse the existing publication authority and preflight facade; add a lazy read-only planner, not a second approval or execution system.

User problem: authorized publication stalls on command shape, wrong worktree, generic failures and stale workflow state.

Approved scope: safe diagnostics, exact command planning, worktree identity, assurance-aware candidate readiness, live PR reuse/recovery, runtime/native invocation guidance, asset delivery guidance and affected-boundary regression. Human approved this concrete boundary in the current chat on 2026-10-11 and explicitly limited mutation to AIPS. LUCAS-LAB is an acceptance reference only.

Existing coverage: personal/high-assurance mode resolver, action binding, mandatory scanner, preflight/Gate, PR checks and installed post-merge reconciliation remain authoritative. No Constitution semantics, native permission rule, external issuer or repository Ruleset is changed. No new Role, Skill, Capability or Gate.

Context cost: helper imports only for prepare/diagnose. No fixed bootstrap addition. Compatibility: additive CLI and exception attributes; original exception messages retained. No stored plan is trusted and no state migration is required.

## Implementation and acceptance

- Phase 0: source and installed AIPS are 0.82.0 at baseline f2bebac5bf927ac7b70b0efa61cb49a7460114d7; local preflight passes and the fixed administrator root is absent (personal). Historical Claude rejection logs are unavailable; old hypotheses remain hypotheses.
- Phase 1: safe fixed reason codes and remediation replace generic publication error display; logs omit exception payload/traceback.
- Phase 2: prepare returns exact SHA/full-ref push and complete PR metadata as native cwd/argv; diagnose validates existing authority without execution.
- Phase 3: explicit worktree root and repository/worktree identity bind observations; changed body, policy, HEAD/base, remote and PR state invalidate the fingerprint. Development assets are preserved; isolated clean engineering worktrees are documented.
- Phase 4: Claude/Gemini existing native hooks receive safe codes and retain merge confirmation; Codex remains ADVISORY. OpenCode arbitrary Shell publication remains unsupported. Host-denied is an explicit observation, never permission.
- Phase 5: each retry re-queries remote evidence, reuses OPEN PRs, rejects duplicates and exact CLOSED candidates, and verifies MERGED head/merge-commit integration including squash. Caller may save the bounded JSON observation; no implicit prompt/body/credential persistence. External grants are never generated or consumed by planning.
- Phase 6: real local bare-Git/worktree, native CLI, hook fixtures, assurance/scanner negative cases; complete exact-candidate local Gate and remote PR/main CI. Fixture metadata does not claim real Claude/Gemini host acceptance. Actual GitHub acceptance is separately verified on this delivery PR.

Asset guidance uses existing creative workflow: master backups, compressed playback delivery, explicit manifest path/use/hash/size/license/deployment-source and LFS deployment verification. Storage choices remain project-specific. No LUCAS-LAB files, publication or Rulesets are changed.

## Architecture and tests

Affected diagram: docs/ARCHITECTURE.md maintenance/publication flow (new observational planner before the existing native authority boundary). Human architecture overview describes the same flow. Existing Human SVG architecture/lifecycle diagrams are N/A: top-level runtime/governance components and authority arrows are unchanged; the new helper is internal to the existing preflight component.

Test boundaries: parser/source/ref; safe exception and log output; mode/trust-root; exact worktree and live base; candidate/history scan; body/fingerprint drift; native facade; existing/closed/duplicate/merged PR recovery; merge intent/method/checks; canonical documentation closure. The Core Matrix binds the final base and exact file set. Full repository graph coverage stays partial; only direct source consumers are reviewed.

Risks: remote observations can change after planning, so native Guard revalidation remains mandatory. Fingerprints never create authorization or server leases. Real Host permissions are separate from fixtures. No automatic merge/rebase, worktree deletion, force reset or credential acquisition.

## Publication proposal

Target: origin / LucasLu3918/ai-product-system, engineering branch codex/plan30-publication-recovery, PR into live main, merge only after exact-candidate local Gate and required PR checks. User explicitly authorized PR and merge in this task; personal mode does not require an external grant. No direct main push, release, admin bypass or branch deletion.

Atomic commit plan: one logical publication-planning/diagnostics capability with its regression and canonical documentation closure; one remote branch update. Remote PR and post-merge main CI remain separate evidence. Independent review enforcement is disabled in the existing Matrix policy; this run uses primary self-review and deterministic checks and does not claim attested independent review.

Local focused evidence: 18 planning/CLI/hook/recovery cases and 31 authority cases pass; canonical docs sync/placement and no-new-helper Ruff findings pass. Complete Gate and live remote observations are required before delivery, not assumed here. Scope drift or a changed candidate requires fresh validation. Rollback uses the single logical commit/PR revert while preserving all pre-existing security rules.

## Files (repository-relative paths and type)

- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` — 修改
- `.aips/review/PLAN30_PUBLICATION.md` — 新增
- `config/documentation-placement.yaml` — 修改
- `config/documentation-sync.yaml` — 修改
- `docs/ARCHITECTURE.md` — 修改
- `docs/human/ARCHITECTURE_OVERVIEW.md` — 修改
- `docs/human/CONFORMANCE.md` — 修改
- `docs/human/DOCUMENTATION_MAP.md` — 修改
- `docs/human/DOCUMENTATION_SYNC.md` — 修改
- `docs/human/EVOLUTION_RADAR.md` — 修改
- `docs/human/HARNESS.md` — 修改
- `docs/human/INSTALLATION.md` — 修改
- `docs/human/MAINTENANCE.md` — 修改
- `docs/human/PROJECT_INTELLIGENCE.md` — 修改
- `docs/human/SECURITY_ASSURANCE.md` — 修改
- `docs/human/TECHNOLOGY_GUIDE.md` — 修改
- `docs/human/USER_GUIDE.md` — 修改
- `docs/human/index.md` — 修改
- `harness/HARNESS_PROTOCOL.md` — 修改
- `harness/adapters/opencode/AGENTS.md` — 修改
- `harness/adapters/opencode/COMPATIBILITY.md` — 修改
- `orchestration/CHANGE_IMPACT.md` — 修改
- `orchestration/CONFORMANCE.md` — 修改
- `orchestration/CORE_CHANGE_TESTING.md` — 修改
- `orchestration/CREATIVE_DIRECTION.md` — 修改
- `orchestration/DETERMINISTIC_SCHEDULER.md` — 修改
- `orchestration/DOCUMENTATION_SYNC.md` — 修改
- `orchestration/EXECUTION_ISOLATION.md` — 修改
- `orchestration/GITHUB_RULESET_POLICY.md` — 修改
- `orchestration/INTEGRATION_GATE.md` — 修改
- `orchestration/ORCHESTRATOR.md` — 修改
- `orchestration/PROJECT_INTELLIGENCE.md` — 修改
- `orchestration/RELEASE_READINESS.md` — 修改
- `orchestration/RUNTIME_CONTEXT.md` — 修改
- `scripts/aips_cli/help.sh` — 修改
- `scripts/governance_guard.py` — 修改
- `scripts/publication_authority.py` — 修改
- `scripts/publication_planning.py` — 新增
- `scripts/publish_preflight.py` — 修改
- `tests/scenarios/240-personal-publication-default.md` — 修改
- `tests/test_publication_planning.py` — 新增
- `tests/validation/publish_preflight_contracts.py` — 修改

- `tests/fixtures/plan21-contract-golden-vectors.yaml` — 修改（新增 CLI 說明的 stdout snapshot；保留 exit/stderr 契約）。
