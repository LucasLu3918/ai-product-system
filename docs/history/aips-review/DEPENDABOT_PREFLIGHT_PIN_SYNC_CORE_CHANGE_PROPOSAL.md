# Dependabot Repository Preflight and Action Pin Sync

## System Improvement Review

- **Appropriateness:** Appropriate. After #350–#353 and #338, six Dependabot PRs still fail on `main` `172128e8`: four pip PRs (#262, #263, #260, #168) in janitor "Repository preflight (fail fast)", and two action re-pins (#340, #259) in repository validation contracts. All six are `PURE_DEPENDENCY_UPDATE` by the #351 predicate (measured below), so the failures are gate wiring, not dependency risk.
- **User problem:** (1) The #351 exemption was wired into three documentation consumers but `scripts/repository_preflight.py` calls the documentation sync evaluator directly, so it still demands filler docs. (2) Ten validation sites copy action commit SHAs as literals; any Dependabot bump of those actions fails a contract that only Human-authored edits to test code can satisfy.
- **Proposed solution:** (1) One shared documentation-sync entry point that consults the existing `pure_dependency_update`; every diff-based sync consumer uses it. (2) Replace literal SHA copies with one shared "pinned action" check built on the existing `dependency_impact.ACTION_LINE` shape: exact action identity, immutable 40-hex SHA, version comment present and not below the reviewed floor, and cross-file consistency where the contract requires it.
- **Existing coverage:** `scripts/dependency_impact.py` (Scenario 221) owns the pure-update predicate and the pinned `uses:` line grammar. `tests/validation/static_contracts.py:388-391` already validates `actions/checkout` / `actions/setup-python` by identity + full SHA rather than a literal, so approach (a) is an existing repository convention.
- **Reuse / extension candidates:** Extend `dependency_impact.py` and `documentation_sync.py`; no new module, capability, Role or Skill.
- **Lower-layer alternative:** Manual sync commits on each Dependabot branch (option c) — rejected, see "Problem 2 options".
- **Context / token cost:** None at bootstrap or per turn.
- **Security / reliability:** Documentation exemption scope is unchanged (same predicate, same allowlist). Pin checks keep identity, immutability and downgrade protection; the only removed property is the literal second copy (analysed below). Any predicate failure still falls back to full rules.
- **Backward compatibility:** Non-dependency candidates produce identical sync results. Contracts become less brittle, not looser, on identity / pinning.
- **Constitution impact:** NO. Human Authority, Protected Safety Boundary, merge and publication authority are untouched.
- **Recommended AIPS solution:** Problem 1 shared entry point + Problem 2 option (a) across all ten pin sites.

## Problem 1 — Repository preflight documentation consistency

### Evidence (local replay against PR heads, base `b6555c31`, the PRs' own base)

| PR | Head | `classify-diff` | `repository_preflight.py` result |
|---|---|---|---|
| #262 coverage | `75ac2e7f` | `PURE_DEPENDENCY_UPDATE` | FAIL: Technology Guide review; `deterministic-execution` Human/Agent docs |
| #263 ruff | `67ace8ce` | `PURE_DEPENDENCY_UPDATE` | FAIL: same as #262 |
| #260 cryptography | `d4c21f2f` | `PURE_DEPENDENCY_UPDATE` | FAIL: Technology Guide; `character-artwork-workflow`; `deterministic-execution` |
| #168 sentence-transformers | `2a6e8988` | `PURE_DEPENDENCY_UPDATE` | FAIL: Technology Guide; `project-intelligence` |
| #340 codex-action | `8b632b8c` | `PURE_DEPENDENCY_UPDATE` | PASS (see latent bug below) |
| #259 scorecard-action | `36bda58f` | `PURE_DEPENDENCY_UPDATE` | PASS (see latent bug below) |

Every failure line is prefixed `Documentation consistency:`; no placement, link or audience errors appear, so wiring the predicate into this one consumer is sufficient for these four heads.

### Root cause

`scripts/repository_preflight.py::run` (lines 200-214) computes `documentation_sync.changed_files_from_git(base, head)` and passes it straight to `documentation_sync.evaluate_changes`. #351's root-cause table enumerated docs-impact, placement and `documentation_sync_contracts`, and its replay exercised exactly those three; `repository_preflight.py` is a fourth caller of the same evaluator and was not in the replay. #338 passed only because of the latent `.github/` bug below, not because the exemption applied.

### Inventory of path-only documentation gates

| # | Gate / consumer | Uses `pure_dependency_update`? | Action |
|---|---|---|---|
| 1 | `publish_preflight.py` docs-impact / plan / run / preview → `publish_preflight_policy.documentation_impact` | Yes (#351) | none |
| 2 | `documentation_placement.placement_errors` (via `repository_preflight` `audit()`, `audit_worktree`, CLI, `aips_cli/project.sh`) | Yes (#351) | none (see LATER note on `head`) |
| 3 | `tests/validation/documentation_sync_contracts.py` diff check | Yes, inline copy | switch to shared entry point (removes duplicate) |
| 4 | `repository_preflight.py::run` sync check | **No** | **wire to shared entry point** |
| 5 | `documentation_sync.py` CLI `main()` with `--base-ref` (no CI caller today; agent/manual use) | **No** | **wire to shared entry point** so local diagnosis matches CI |
| — | Markdown links, docs build trigger, documentation audience, Core Change Test Matrix, CI validation plan | n/a | Not documentation-sync gates (content / static / job selection / out of scope) |

### Design

- `scripts/documentation_sync.py`: add `evaluate_candidate(base, head, config, root=ROOT) -> (errors, exemption)`. It computes changed files, calls `dependency_impact.pure_dependency_update(base, head, root)`, and returns `([], scope)` only when status is `PURE_DEPENDENCY_UPDATE` **and** `sorted(set(files)) == scope["files"]` (the same equality guard #351 uses). Otherwise returns `evaluate_changes(files, config)`. Import of `dependency_impact` is lazy; any exception inside the predicate already yields `NOT_PURE`, so failure means full rules.
- `repository_preflight.run`, `documentation_sync_contracts`, and the `documentation_sync.py` CLI call `evaluate_candidate`. No new predicate, allowlist or policy key.

### Latent bug found (NOT in scope; proposed as a follow-up)

`documentation_sync.evaluate_changes` normalizes paths with `str(x).strip().lstrip("./")`, which strips leading `.` **characters**, turning `.github/workflows/x.yml` into `github/workflows/x.yml`. Every `.github/**` trigger in `config/documentation-sync.yaml` (Technology Guide `.github/workflows/**`, `evolution-radar`, `publication-preflight` → `validate.yml`, `documentation-platform`, `execution-isolation`, …) is therefore dead in the sync gate. Fixing it makes the sync gate stricter for every workflow edit, so it needs its own review. This proposal makes that future fix safe for Dependabot workflow PRs, because the pure-update exemption will already be wired into every sync consumer.

## Problem 2 — Literal action SHA copies

### Evidence

Contract replay (`static_contracts` + the five pin contract modules) at PR heads:

| PR | Errors |
|---|---|
| #340 | `Evolution Radar analyzer workflow missing: openai/codex-action@86365089…`; `evolution-radar.yml does not match configured Codex Action commit`; `evolution-decision.yml does not match configured Codex Action commit` |
| #259 | `Scorecard workflow missing required advisory control: ossf/scorecard-action@55891bbd…` |
| `main` `172128e8` | none |

Upstream verification (read-only GitHub API, tag peeled to commit):

| Action | Tag | Tag object | Commit | Note |
|---|---|---|---|---|
| `openai/codex-action` | `v1.12` | `cac08775…` | `86365089…` | current pin |
| `openai/codex-action` | `v1.13` = `v1` | `83eeca45…` / `1d82a3db…` | `bdf19a4a…` | #340 target, legitimate |
| `ossf/scorecard-action` | `v2.4.4` | `55891bbd…` | `2d114668…` | **current pin is the annotated tag object SHA, not the commit**; #259 corrects it to the commit |

### Pin sites (all literal SHA copies outside workflows)

1. `tests/validation/security_workflow_contracts.py:15` — `actions/dependency-review-action@a1d282b3…` ("verified v5.0.0")
2. `tests/validation/security_workflow_contracts.py:29` — `ossf/scorecard-action@55891bbd…` (#259)
3. `tests/validation/security_workflow_contracts.py:46` — `google/osv-scanner-action/.github/workflows/osv-scanner-reusable.yml@c7c7bcb0…`
4. `tests/validation/security_workflow_contracts.py:50` — `gitleaks/gitleaks-action@e0c47f4f…`
5. `tests/validation/dependency_review_contracts.py:33` — `actions/dependency-review-action@a1d282b3…`
6. `tests/validation/evolution_governance_contracts.py:258` — `openai/codex-action@86365089…` (#340)
7. `tests/validation/evolution_governance_contracts.py:301-309` comparing `config/evolution-analyzer.yaml:10` and `config/evolution-trial.yaml:10` `action_commit` (#340). No script reads `action_commit`; only this contract.
8. `tests/validation/publish_preflight_contracts.py:62-64` — `actions/deploy-pages@368f8252… # v5.0.1`, `actions/upload-artifact@b7c566a7… # v6.0.0` (intent: Node 24 floor)
9. `tests/validation/repository_health_contracts.py:299,318` — `actions/upload-artifact@043fb46d…` in `validate.yml` / `repository-health.yml`
10. `tests/evidence/publish_preflight_lifecycle.py:1006-1007` — same as 8

Sites 8–10 will block #339 (upload-artifact) on contracts even after its separate Core Change Test Matrix issue is resolved. `.aips/review/PLAN27_MAINTENANCE_EVIDENCE.yaml:87` is historical evidence and stays as is.

### Options and security analysis

The pin's security purpose is: the workflow executes an **immutable commit of the intended action repository**, and any change to that commit is **visible to and approved by a Human**. The literal second copy adds one property: a pin change cannot land unless the same PR also edits a test/config file.

| Property | Today | (a) read from workflow | (b) widen pure predicate to config/test sync | (c) manual sync commit per PR |
|---|---|---|---|---|
| Action identity (owner/repo/path) exact | Yes | Yes (exact identity argument) | Yes | Yes |
| Immutable 40-hex SHA, no tag/branch | Yes | Yes | Yes | Yes |
| Downgrade blocked | Partly (only via literal) | Yes: version comment ≥ reviewed floor, plus predicate `ACTION_DOWNGRADE` | Yes | Yes |
| Node 24 / reviewed-version floor | Literal | Yes: `min_version` floor per site | Literal | Literal |
| Same SHA across paired workflows (evolution) | Via config | Yes: explicit cross-file equality | Via config | Via config |
| Pin change requires editing a second file | Yes | **No** | Yes, but Human writes both | Yes, Human writes both |
| Impostor commit (fork commit reachable through parent repo path) caught automatically | Only if attacker forgets the second copy; an attacker editing both files defeats it | No | No | No |
| Dependabot PR mergeable without Human-authored commit | No | **Yes** | No — Dependabot never edits config/tests | No |
| Documentation exemption scope | — | unchanged | **widened** to `tests/validation/*.py` and `config/*.yaml` (code; Python literal parsing needed) | unchanged, but candidate becomes `NOT_PURE`: measured **10** docs for #340, **5** for #259 |
| Dependabot keeps rebasing branch | — | yes | no (foreign commit) | no (foreign commit) |
| Repeats on every future bump | — | no | yes | yes |

Assessment:

- **(a)** removes only the "second literal" tripwire. That tripwire never defeated a deliberate attacker (who edits both files in one PR) and is not an impostor-commit check; it is a reviewer-attention device. Attention is preserved by: the PR diff itself, the #351 classification (`repinned_same_version: true`, `human_review_required: true`), Dependency Review, Scorecard, Integration Gate, required checks and Human merge approval. Every other protection is kept or strengthened (explicit downgrade floor, explicit cross-file equality, `uses:` grammar shared with the predicate). It also matches the existing `actions/checkout` / `actions/setup-python` convention.
- **(b)** widens a documentation exemption into code and test files, needs a Python-literal parser for an exemption, and still does not unblock Dependabot (someone must push the sync commit). More attack surface, no gain over (c). **Reject.**
- **(c)** changes no gate but costs 5–10 filler docs per PR (measured), stops Dependabot auto-rebase, and repeats forever. **Reject as process**; acceptable only as a one-off if (a) is declined.

**Recommendation: (a)**, with the reviewer-side mitigation documented: for any pin change, the reviewer peels the version tag to its commit (as done above for #259 / #340). An automated, advisory tag-peel check is listed as a LATER candidate.

### Design for (a)

- `scripts/dependency_impact.py`: add `pinned_action_references(text, action)` and `require_pinned_action(text, action, *, label, min_version=None, expected_count=None) -> list[str]`, built on the existing `ACTION_LINE`, `PINNED_SHA` and `_release` (single grammar for "pinned `uses:` line" shared with the pure-update predicate). Rules:
  - At least one (or exactly `expected_count`) `uses: <action>@<ref>` line; `action` compared exactly.
  - Every reference to that action is a 40-hex SHA; any `@tag` / `@branch` occurrence fails.
  - A version comment is present; with `min_version`, its release segment is ≥ the floor.
  - Returns stable messages (`<label> must pin <action> to an immutable full commit SHA`, `… below reviewed floor …`).
- Floors are the currently reviewed versions: dependency-review `v5.0.0`, scorecard `v2.4.4`, codex-action `v1.12`, deploy-pages `v5.0.1`, upload-artifact `v6.0.0` (e2b) and the current comment for `043fb46d…`, osv-scanner and gitleaks (read from `main` at implementation time).
- Evolution: `config/evolution-analyzer.yaml` / `config/evolution-trial.yaml` replace `action_commit: <sha>` with `action: openai/codex-action` (identity, not version). The contract requires both workflows to pin that identity and to use the **same** SHA; `codex_version` check is unchanged.
- Sites 1–10 call the helper; `static_contracts.py:388-391` is migrated to it for consistency.

## Proposed Scope

### In scope

- `scripts/documentation_sync.py` (`evaluate_candidate`, CLI uses it)
- `scripts/repository_preflight.py` (sync check via `evaluate_candidate`)
- `scripts/dependency_impact.py` (`pinned_action_references`, `require_pinned_action`)
- `tests/validation/documentation_sync_contracts.py`, `static_contracts.py`, `security_workflow_contracts.py`, `dependency_review_contracts.py`, `evolution_governance_contracts.py`, `publish_preflight_contracts.py`, `repository_health_contracts.py`
- `tests/evidence/publish_preflight_lifecycle.py` (site 10 + repository_preflight exemption fixtures), `tests/evidence/dependency_impact_lifecycle.py` (helper fixtures)
- `config/evolution-analyzer.yaml`, `config/evolution-trial.yaml` (`action_commit` → `action`)
- `tests/scenarios/221-dependency-update-risk-classification.md` (extend; no new scenario)
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` (required: `scripts/repository_preflight.py` is in `matrix_required_paths`)
- Documentation closure below; `CHANGELOG.md` / `VERSION` per version policy
- This proposal

### Out of scope

- #261 (real `pyee` / `playwright` conflict), #337 / #339 Core Change Test Matrix on `validate.yml`, branch protection, required-check definitions, auto-merge, merging or rebasing any Dependabot PR.
- Fixing the `lstrip("./")` latent bug (follow-up).
- Any change to the pure-update allowlist, size limits or line shapes.
- Workflow edits (no `.github/workflows/*` change).

## Impact

### Affected boundaries

| Boundary | Change |
|---|---|
| Repository preflight (janitor fail-fast, `publish_preflight.py run` subprocess) | Sync check honours the existing exemption |
| Documentation sync CLI / contracts | Shared entry point; duplicate inline logic removed |
| Dependency Update Risk Classification (Scenario 221) | Gains a read-only pin helper; predicate unchanged |
| Supply-chain / evolution / publish / repository-health validation contracts | Literal SHA → identity + immutability + floor + consistency |
| Evolution adapter config | `action_commit` → `action` identity key |

### Tests / Validation matrix

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| `evaluate_candidate` + preflight wiring | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | No UI |
| Pin helper | YES | YES | N/A | YES | N/A | YES | N/A | N/A | YES | Pure function |
| Ten pin sites | YES | N/A | YES | YES | N/A | YES | N/A | N/A | YES | Contracts only |
| Evolution config key | YES | N/A | YES | YES | N/A | N/A | YES (revert-only) | N/A | YES | Static file |
| Repository delivery | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | Full local Gate + remote checks |

Positive (must pass), replayed by overlaying the candidate's changed files onto each real PR head in a scratch worktree:

1. #262 `75ac2e7f`, #263 `67ace8ce`, #260 `d4c21f2f`, #168 `2a6e8988`: `repository_preflight.py --base <base> --head HEAD` → `PASSED`; `documentation_sync.py --base-ref <base>` → valid with exemption.
2. #340 `8b632b8c`: evolution, security, dependency-review, publish-preflight and repository-health contracts → 0 errors.
3. #259 `36bda58f`: same contract set → 0 errors.
4. `main` (candidate itself): full contract set → 0 errors.
5. Synthetic: same-version re-pin, minor bump across paired workflows with identical SHA.

Negative (must fail with the stated message, fixtures in temporary Git repos / in-memory text):

1. Pip bump **plus** any doc/script edit → `NOT_PURE`, sync errors identical to today.
2. Pip range edit / non-dependency `requirements*.txt` change → sync errors identical to today.
3. `repository_preflight` with an unresolvable base → predicate `GIT_ERROR`, full rules, existing error.
4. Policy `documentation_exemption.enabled: false` → full sync rules.
5. Pin → `@v4` tag, `@main` branch, short SHA → immutability error.
6. Action identity swap (`ossf/scorecard-action` → `evil/scorecard-action`) → missing-pin error.
7. Version comment removed, or below floor (`# v2.4.3`, `# v5.0.0` for deploy-pages) → floor error.
8. Evolution radar and decision pinned to different SHAs → consistency error.
9. Second unpinned reference of the same action added alongside a pinned one → immutability error.
10. Evolution config still carrying `action_commit` or missing `action` → contract error.

Required evidence before review: focused lifecycle suites, `python scripts/capability_registry.py check`, full local Gate (`publish_preflight.py run`), candidate secret scan, remote `repository` check on the PR; after merge, rebased #262/#263/#260/#168/#340/#259 checks.

### Secret / Credential Impact

Secrets required: NO. Fixtures use synthetic SHAs; upstream tag lookups are read-only and not part of tests.

### Documentation sync plan

Measured with `docs-impact --planned-path` for the in-scope files: 20 documents across `capability-registry`, `publication-preflight`, `evolution`, `documentation-governance`, `p16-dependency-risk-classification`, `p17-required-files-parity-pilot`, `repository-health`, `security`, `deterministic-execution`, `scenario-conformance`, `independent-review-isolation`. Planned content in each configured H2:

- `docs/human/CONFORMANCE.md`, `orchestration/CONFORMANCE.md` — Scenario 221: repository preflight honours the exemption; pin helper rules and negative cases.
- `docs/human/DOCUMENTATION_SYNC.md`, `orchestration/DOCUMENTATION_SYNC.md`, `docs/human/DOCUMENTATION_MAP.md` — Deterministic protection: single `evaluate_candidate` entry point for every diff-based sync consumer.
- `docs/human/SECURITY_ASSURANCE.md` — Release Security Gate: action pins validated by identity + immutable SHA + reviewed floor; Human tag-peel review for re-pins.
- `docs/human/MAINTENANCE.md` — Public repository / CI consistency: how Dependabot pip and action PRs pass; what remains Human-reviewed.
- `docs/human/EVOLUTION_RADAR.md`, `docs/human/EVOLUTION_RADAR_OVERVIEW.md`, `orchestration/EVOLUTION_RADAR.md`, `orchestration/EXECUTION_ISOLATION.md` — adapter config names the action identity; the SHA lives only in the workflows.
- `docs/human/TECHNOLOGY_GUIDE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, `docs/human/USER_GUIDE.md`, `docs/human/SYSTEM_REFERENCE.md`, `orchestration/CORE_CHANGE_TESTING.md`, `orchestration/DETERMINISTIC_SCHEDULER.md`, `orchestration/INTEGRATION_GATE.md`, `orchestration/ORCHESTRATOR.md`, `orchestration/REPOSITORY_HEALTH.md` — concise notes in required sections that their own gates are unchanged.

The closure is recomputed from the real diff before commit; documents that drop out are not edited.

### Diagrams

- `docs/ARCHITECTURE.md` Mermaid: N/A — no component or trust-boundary change.
- Human SVG diagrams: N/A — same lifecycle.

## Rollback

Revert the single PR. No data migration; the config key rename reverts with it. Partial rollback: Problem 1 and Problem 2 touch disjoint call sites and can be reverted independently. Emergency switch for Problem 1 remains `documentation_exemption.enabled: false` in `config/dependency-policy.yaml` (already validated).

## Additional optimization candidates (not in scope)

| Candidate | Benefit | Timing |
|---|---|---|
| Fix `lstrip("./")` in `documentation_sync.evaluate_changes` | Restores dead `.github/**` sync triggers | NEXT — separate Core Change; safe for Dependabot once this lands |
| `placement_errors` honours caller `head` instead of `"HEAD"` | Correct when `--head` ≠ checkout; all current callers pass `HEAD` | LATER |
| Advisory CI check: pinned SHA equals the peeled upstream tag commit named in the version comment | Automates the impostor-commit review | LATER — needs network + rate-limit handling |
| #337 / #339 `validate.yml` matrix requirement | Unblocks two remaining action PRs | LATER — governance-core path |

## Risks

- Version comments are text written by the PR author; the floor check guards accidental downgrades, not deception. Deception is covered by Human review (and the LATER tag-peel check).
- Dependabot PRs execute CI from their own head; after merge they need a rebase before they benefit.
- #261 will become documentation-exempt but must still fail its dependency resolution; this proposal does not hide that.

## Proposed Implementation Order

1. Fixtures reproducing today's failures (pip sync, #340 / #259 contract shapes).
2. `evaluate_candidate` + wiring (Problem 1); replay #262 / #263 / #260 / #168.
3. Pin helper + ten sites + evolution config (Problem 2); replay #340 / #259.
4. Negative tests; documentation closure; Core Change Test Matrix; `capability_registry.py check`; full local Gate.
5. Commit on `claude/preflight-pin-sync-f07b9a`. Push / PR only after the Git Publish Approval Gate and a fresh Human confirmation in this session.

## Approval

Status: APPROVED
Approved by: User, directly in this session (an earlier relayed approval was not treated as sufficient)
Approved at: 2026-10-20 (Asia/Taipei)
Approval record: 「核准，依推薦執行」 — D1 option (a); D2 all ten pin sites; D3 replace `action_commit` with `action: openai/codex-action`. The `lstrip("./")` latent bug stays out of scope. Push / PR remain subject to the Git Publish Approval Gate and a fresh Human confirmation.
Proposal fingerprint: sha256:f8bfe850ee3152152fc054379847d3591260e6d650018b7235fa3e2b77e5ff46 (proposal bytes preceding this Approval section)
Scope fingerprint: In scope / Out of scope sections as approved; recomputed against the final diff before commit.
