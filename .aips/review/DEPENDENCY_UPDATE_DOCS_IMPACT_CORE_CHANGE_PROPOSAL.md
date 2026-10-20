# Pure Dependency Update Documentation Impact Exemption

## System Improvement Review

- **Appropriateness:** Appropriate. Ten open Dependabot PRs (#168, #259–#263, #337–#340) cannot pass the required `repository` check, and the repository has never merged a Dependabot PR. The blocker is documentation impact, not base drift: a one-line action SHA bump in `.github/workflows/scorecard.yml` (#338) is told to update five Human/Agent docs, and a two-line `coverage` pin bump (#262) is told to update thirteen.
- **User problem:** Pure version/pin updates carry no behavior that any canonical document describes, yet path-based documentation triggers treat them as behavior changes. The demanded document edits would be filler that adds no truth and cannot be produced by Dependabot.
- **Proposed solution:** Recognize a strict, deterministic "pure dependency update" diff shape and narrow the documentation requirement for that shape only, handing the evidence to the existing Dependency Update Risk Classification (Scenario 221).
- **Existing coverage:** `scripts/dependency_impact.py` + `config/dependency-policy.yaml` (Scenario 221) already classify pip / GitHub Actions dependencies and keep `automatic_merge_authorized: false`. Nothing today inspects diff *content* for documentation purposes; all three documentation gates are path-only.
- **Reuse / extension candidates:** Extend `scripts/dependency_impact.py` (Scenario 221 owner) with a diff-shape classifier instead of adding a new module, capability or Skill. Reuse `classify_dependency` for per-item risk evidence.
- **Lower-layer alternative:** Removing `.github/workflows/scorecard.yml`, `requirements*.txt` or `constraints/tested.txt` from placement triggers was considered and rejected: real behavior changes to those files (new steps, `run:` edits, new dependencies, range changes) must keep their documentation requirements. Content-shape detection is the narrowest layer that separates the two.
- **Context / token cost:** None at bootstrap or per turn. One deterministic `git diff` parse per documentation check.
- **Security / reliability:** Exemption affects only documentation requirements. Secret scan, content safety, commit identity, Integration Gate, Core Change Test Matrix, required checks and Human merge approval are unchanged. Any ambiguity, parse failure or classifier failure falls back to the full existing rules (fail-closed toward *more* documentation, never less).
- **Backward compatibility:** Additive. Every non-matching candidate produces byte-identical requirements to today. `documentation_impact(files, root)` keeps its signature; new behavior is an optional argument.
- **Constitution impact:** NO.
- **Why:** Human Authority, Protected Safety Boundary and merge/publication authority are untouched. The change narrows a documentation-completeness heuristic for a provably behavior-free diff shape and records why.
- **Recommended AIPS solution:** Same as proposed, with three consumers sharing one predicate (see "Root cause").
- **Additional optimization candidates:** see dedicated section; none included in scope.

## Root cause (evidence from `df79357e`)

Three independent gates evaluate the same changed-path list, and all of them are path-only:

| Gate | Where | Why #338 fails |
|---|---|---|
| Documentation impact closure (CI janitor "Fast documentation impact precheck", and `build_plan` blocker inside `publish_preflight.py run`) | `scripts/publish_preflight_policy.py::documentation_impact` | `scorecard.yml` matches placement `p14-maintenance-governance` → requires `MAINTENANCE.md`, `SECURITY_ASSURANCE.md`, `TECHNOLOGY_GUIDE.md`, `docs/human/CONFORMANCE.md`, `orchestration/CONFORMANCE.md`. The closure is **transitive**: the newly required `orchestration/CONFORMANCE.md` itself triggers `scenario-conformance`, and `.github/workflows/**` triggers `technology_guide`. |
| Documentation sync (repository validation) | `tests/validation/documentation_sync_contracts.py` → `scripts/documentation_sync.py::evaluate_changes` over `git diff base...HEAD` | `technology_guide` trigger `.github/workflows/**` / `requirements*.txt` requires `TECHNOLOGY_GUIDE.md`. |
| Documentation placement (repository validation and `preview`) | `scripts/documentation_placement.py::placement_errors` | Every triggered placement doc must be changed and must have added lines inside its allowed H2 sections. |

Measured local `docs-impact` results against `origin/main` (`df79357e`):

| PR | Change | Required additions | Triggered placement rules |
|---|---|---|---|
| #338 | 1 `uses:` SHA line in `scorecard.yml` | 5 | `p14-maintenance-governance`, `scenario-conformance` |
| #262 | `coverage==` in `constraints/tested.txt` + `requirements-validation.txt` | 13 | `content-safety`, `independent-review-isolation`, `security`, `deterministic-execution`, `scenario-conformance` |
| #337 | 2 `uses:` SHA lines (`docs-site.yml`, `validate.yml`) | 14 | 9 rules |
| #168 | `sentence-transformers==` in `requirements-semantic-trial.txt` | 6 | `project-intelligence` |

Fixing only the janitor step is insufficient: the `repository` job would then fail on the placement and sync gates. All three must consult the same predicate.

## Definition: Pure Dependency Update (deterministic)

A candidate is `PURE_DEPENDENCY_UPDATE` only if **every** condition holds; otherwise it is `NOT_PURE` with a stable reason code and the full existing rules apply unchanged.

### Candidate-level conditions

1. Diff is computed as `git diff --no-renames --no-ext-diff --no-textconv --full-index -U0 <base>...<head>` (same merge-base semantics as `changed_files`). Working-tree mode (`preview`) uses `git diff <base> --` and treats any untracked file as `NOT_PURE`.
2. Every changed path matches one allowlisted pattern exactly (`fnmatchcase`):
   - `.github/workflows/*.yml`, `.github/workflows/*.yaml`
   - `requirements*.txt` (repository root only)
   - `constraints/*.txt`
3. Every file entry is a plain in-place modification: no add, delete, rename, copy, mode change, symlink, submodule or binary (`--numstat` must report numeric counts; `--summary` must be empty).
4. No `--planned-path` was supplied (prospective paths cannot be content-verified).
5. Bounded size: at most 20 files and 100 changed line pairs; beyond that → `NOT_PURE: SIZE_LIMIT`.
6. Each `-U0` hunk has equal removed and added line counts; lines are paired in order (removed[i] ↔ added[i]). Any unpaired line → `NOT_PURE`.
7. Lines must be ASCII, must not contain `\r` or tab characters other than leading indentation spaces, and must match exactly one of the two shapes below (`re.fullmatch`, `re.ASCII`).

### Shape A — pinned GitHub Action reference (workflow files only)

```
^(?P<prefix> *(?:- +)?)uses: (?P<action>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./-]+)?)@(?P<sha>[0-9a-f]{40})(?: +# +(?P<ver>v?[0-9]+(?:\.[0-9]+){0,3}))?$
```

Pair rules:
- `prefix` identical (same indentation, same list position) and `action` identical (same owner/repo/path; no owner swap, no `./` local action, no `docker://`).
- Both sides pinned to a 40-hex SHA (unpinned tag / branch on either side → `NOT_PURE: UNPINNED_REFERENCE`).
- The pair must actually change the SHA or the version comment.
- Version comment presence must be identical on both sides. When both present, the new version must be numerically `>=` the old (`ACTION_DOWNGRADE` otherwise). An equal version with a new SHA (Dependabot re-pin, e.g. #259, #340) is allowed and recorded as `repinned_same_version: true` for reviewers.

### Shape B — exact pip pin (requirements / constraints files only)

```
^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<ver>[0-9]+(?:\.[0-9]+){0,3})$
```

Pair rules:
- PEP 503-normalized `name` identical.
- New version strictly greater than old by numeric release-segment comparison (`PIP_DOWNGRADE` / `PIP_NO_CHANGE` otherwise).
- No extras, markers, hashes, comments, ranges (`>=`, `<`, `~=`), pre/post/dev/local versions or URLs; those are out of shape → full rules. (Example: `requirements.txt` range lines such as `PyYAML>=6.0.3,<7` are never exempt.)

### Classification evidence (Scenario 221 reuse)

For each recognized update the predicate calls the existing `classify_dependency` (`ecosystem` = `github-actions` for Shape A using `owner/repo`, `pip` for Shape B) and attaches `classification`, `risk`, `required_evidence` and `human_review_required`. If policy validation or any item returns `BLOCKED`, the candidate becomes `NOT_PURE: CLASSIFIER_BLOCKED`. The result always carries `automatic_merge_authorized: false` and `human_decision_required: true`.

## Exemption scope

When `PURE_DEPENDENCY_UPDATE`:

| Gate | New behavior |
|---|---|
| `documentation_impact` (`docs-impact`, `plan`, `run`, `preview`) | Returns `complete: true`, empty `required_additions`, and a new `dependency_update_exemption` block (status, reason, per-item classification, `policy_sha256`, diff digest). Placement/sync rules are still listed as `suppressed_rules` for transparency. |
| `documentation_placement.placement_errors` | Returns no placement errors for the candidate (static config errors still reported). |
| `documentation_sync_contracts` diff check | Skips the diff-based `evaluate_changes` call; static config contracts still run. |
| GitHub Step Summary | Prints `Documentation impact: EXEMPT (pure dependency update)` plus each item's class/risk, instead of the required list. |

Exempted: **documentation requirements only**. Not exempted: secret scan, content safety, commit identity, Core Change Test Matrix (`matrix_required_paths`), Integration Gate, workflow contracts, required checks, branch protection and Human merge approval.

Decision point for the user: HIGH-risk classes (`SECURITY_SENSITIVE` e.g. `cryptography` #260, `SEMANTIC_RUNTIME` e.g. `sentence-transformers` #168, `UNCLASSIFIED`).
- **Option A (recommended):** exempt documentation for every class and surface `human_review_required: true` in the report. Documents are not the evidence those classes require; withholding the exemption would leave them blocked forever without adding review quality.
- **Option B:** exempt only `LOW` / `MEDIUM`; HIGH stays on full documentation rules.

## Security / abuse analysis

| Attempt | Result |
|---|---|
| Sneak a `run:` / `with:` / `env:` / permissions edit next to a SHA bump | Unpaired or out-of-shape line → `NOT_PURE` |
| Add a new step or a new action | Added line without removed partner → `NOT_PURE` |
| Swap action owner (`actions/checkout` → `evil/checkout`) | `ACTION_IDENTITY_CHANGED` |
| Switch to unpinned tag / branch, or local `./` / `docker://` action | Out of shape / `UNPINNED_REFERENCE` |
| Downgrade a pin (action comment or pip) | `ACTION_DOWNGRADE` / `PIP_DOWNGRADE` |
| Change a version range, add a dependency, add markers/hashes | Out of shape |
| Touch any other file (code, docs, local composite action, policy) | `PATH_NOT_ALLOWED` — whole candidate falls back to full rules |
| Rename / new / delete / mode change / binary / CRLF / Unicode look-alikes | Rejected by file-entry and ASCII checks |
| Claim exemption via PR label, author or commit message | Not consulted; content-only, reproducible locally and in CI |
| Malicious commit behind a legitimate-looking SHA | Not detectable by documentation either; unchanged coverage from dependency-review, CI_ACTION `action_reference_review`, Integration Gate and Human merge approval |
| Huge grouped update hiding intent | `SIZE_LIMIT` (20 files / 100 pairs) |

Fail direction: any parser exception, git error or classifier error yields `NOT_PURE` → existing (stricter) behavior. The exemption can never make a gate stricter-to-looser for a non-matching diff.

## Proposed Scope

### In scope

- `scripts/dependency_impact.py`: add `pure_dependency_update(base, head | None, root)` with stable reason codes; add CLI `classify-diff --base --head` for local evidence.
- `config/dependency-policy.yaml`: add a validated `documentation_exemption` block (allowed path patterns, size limits, `enabled: true`, HIGH-risk choice per the decision above). Validation rejects broad patterns (`**`, `*` alone, docs/scripts paths).
- `scripts/publish_preflight_policy.py`: optional `dependency_update` argument to `documentation_impact`.
- `scripts/publish_preflight.py`: pass the predicate result from `docs-impact`, `build_plan`, `preview_candidate`; Step Summary rendering.
- `scripts/documentation_placement.py`: early exemption in `placement_errors` when the predicate is pure.
- `tests/validation/documentation_sync_contracts.py`: skip the diff-based sync check when pure.
- Tests: extend `tests/evidence/dependency_impact_lifecycle.py` (temporary Git fixture repos) and `tests/evidence/publish_preflight_lifecycle.py`; extend Scenario 221 instead of creating a new scenario.
- Documentation closure for this change itself (see "Documentation sync plan"), `CHANGELOG.md`/`VERSION` if version policy requires, `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml` (required because `scripts/publish_preflight.py` is a `matrix_required_paths` entry).

### Out of scope

- `--admin`, branch protection, required-check contexts, the `repository` check definition, or auto-merge.
- Core Change Test Matrix requirement for `.github/workflows/validate.yml` (affects #337, #339; see LATER candidate).
- Changing the transitive closure algorithm or any placement/sync rule's triggers for non-dependency changes.
- Rebasing, editing or merging any Dependabot PR (separate, Human-approved publication step).

## Expected Files / Modules

- `scripts/dependency_impact.py`
- `config/dependency-policy.yaml`
- `scripts/publish_preflight_policy.py`
- `scripts/publish_preflight.py`
- `scripts/documentation_placement.py`
- `tests/validation/documentation_sync_contracts.py`
- `tests/evidence/dependency_impact_lifecycle.py`
- `tests/evidence/publish_preflight_lifecycle.py`
- `tests/scenarios/221-dependency-update-risk-classification.md`
- `tests/scenario_coverage.yaml` (only if Scenario 221 evidence list changes)
- `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`
- Documentation listed below; `CHANGELOG.md`, `VERSION` as required.
- This proposal.

## Impact

### Architecture / Contracts

No new service, dependency or capability. `documentation_impact` output gains an additive `dependency_update_exemption` field; existing keys keep meaning. `scripts/dependency_impact.py` gains one function and one subcommand. The janitor step needs no workflow edit (its install of `PyYAML` only is sufficient; no `packaging` import).

### Data / Migration

None. Static policy additions only.

### Compatibility / Rollback

Non-matching candidates are unchanged. Rollback: revert the single PR, or set `documentation_exemption.enabled: false`.

### Tests / Validation

| Affected boundary | Static/Lint | Unit | Integration | Contract | E2E | Security | Migration/Recovery | CLI/Harness | Docs/Schema | N/A reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Diff-shape predicate | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | No UI |
| `documentation_impact` exemption | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | No migration |
| Placement / sync gates | YES | YES | YES | YES | N/A | YES | N/A | N/A | YES | Repository validation only |
| Policy config validation | YES | YES | N/A | YES | N/A | YES | N/A | N/A | YES | Static file |
| Repository delivery | YES | YES | YES | YES | N/A | YES | N/A | YES | YES | Full local Gate + remote checks |

Positive cases (must be `PURE_DEPENDENCY_UPDATE`, `complete: true`, placement and sync clean):

1. Single workflow SHA + version comment bump (#338 shape).
2. Same-version SHA re-pin (#259 / #340 shape) — pure, `repinned_same_version: true`.
3. Grouped action update across 11 workflow files including a major bump (#339 shape).
4. `constraints/tested.txt` + `requirements-validation.txt` pip bump (#262 shape).
5. Same package bumped in three files (#260 shape).
6. Real PR heads #338 and #262 replayed locally against `df79357e` (or the then-current `main`): `docs-impact --require-complete` exit 0, plus `documentation_placement` and documentation sync contracts clean.

Negative cases (must be `NOT_PURE` with the stated reason and requirements identical to today):

1. SHA bump plus an extra `with:` / `run:` / `env:` line edit — `UNPAIRED_LINE` / `OUT_OF_SHAPE`.
2. Newly added `uses:` step — `UNPAIRED_LINE`.
3. `run:` command edit alone — `OUT_OF_SHAPE`.
4. Action downgrade by comment, and pip downgrade — `ACTION_DOWNGRADE` / `PIP_DOWNGRADE`.
5. Pinned SHA → unpinned tag (`@v4`), and unpinned → unpinned — `UNPINNED_REFERENCE`.
6. Action owner/repo swap — `ACTION_IDENTITY_CHANGED`.
7. Local `./.github/actions/...` and `docker://` references — `OUT_OF_SHAPE`.
8. Pip range edit (`>=6.0.3,<7` → `>=6.0.4,<7`), extras/markers/hash/pre-release — `OUT_OF_SHAPE`.
9. Dependency bump plus any non-allowlisted path (docs, scripts, composite action) — `PATH_NOT_ALLOWED`.
10. New / deleted / renamed allowlisted file, mode change, binary, CRLF, non-ASCII look-alike — rejected.
11. `--planned-path` supplied — `PLANNED_PATHS_PRESENT`.
12. Size limit exceeded — `SIZE_LIMIT`.
13. Invalid dependency policy / classifier `BLOCKED` — `CLASSIFIER_BLOCKED`.
14. Working-tree preview with an untracked file — `UNTRACKED_PRESENT`.
15. Git error (unresolvable base) — `GIT_ERROR`, full rules.
16. Policy `documentation_exemption.enabled: false` or broad allowlist pattern — disabled / config validation error.

Required release/CI evidence: focused lifecycle suites, `python scripts/capability_registry.py check`, full repository Integration Gate via `publish_preflight.py run`, candidate secret scan, remote `repository` check on this PR, then re-run of #338 / #262 checks after merge.

### Secret / Credential Impact

Secrets required: NO. Fixtures use synthetic SHAs and package names only.

### Documentation sync plan

This change itself triggers (measured with `docs-impact --planned-path`) 17 documents across placement rules `publication-preflight`, `content-safety`, `documentation-governance`, `documentation-platform`, `independent-review-isolation`, `p16-dependency-risk-classification`, `security`, `deterministic-execution`, `scenario-conformance`. Planned content, each placed in its configured canonical H2:

- `docs/human/CONFORMANCE.md`, `orchestration/CONFORMANCE.md` — Scenario 221 section: pure-dependency diff shape, documentation-only exemption, negative cases.
- `docs/human/MAINTENANCE.md` — Public repository / CI consistency: why Dependabot PRs pass documentation impact and what remains Human-reviewed.
- `docs/human/DOCUMENTATION_SYNC.md`, `orchestration/DOCUMENTATION_SYNC.md`, `docs/human/DOCUMENTATION_MAP.md` — Deterministic protection: the exemption predicate and its fail-closed fallback.
- `docs/human/SECURITY_ASSURANCE.md` — Release Security Gate: exemption does not touch security gates; abuse table summary.
- `docs/human/TECHNOLOGY_GUIDE.md`, `docs/human/ARCHITECTURE_OVERVIEW.md`, `docs/human/USER_GUIDE.md`, `docs/human/INSTALLATION.md`, `docs/human/PROJECT_INTELLIGENCE.md`, `orchestration/CONTENT_SAFETY_BOUNDARY.md`, `orchestration/CORE_CHANGE_TESTING.md`, `orchestration/DETERMINISTIC_SCHEDULER.md`, `orchestration/INTEGRATION_GATE.md`, `orchestration/ORCHESTRATOR.md` — concise one-paragraph notes in their required sections stating that documentation impact may report `EXEMPT` for verified pure dependency updates and that their own gates are unchanged.

If the final diff avoids a trigger file, the corresponding documents drop out; the closure will be recomputed from the real diff before commit.

### Diagrams

- `docs/ARCHITECTURE.md` Mermaid: N/A — no component or trust-boundary change.
- Human SVG architecture/lifecycle diagrams: N/A — same lifecycle; one additional deterministic check inside an existing gate.

## Additional optimization candidates (not in scope)

| Candidate | Benefit | Timing |
|---|---|---|
| Treat a pure dependency diff on `.github/workflows/validate.yml` as not matrix-required | Unblocks #337 / #339, which will otherwise still fail the Core Change Test Matrix binding | LATER — `validate.yml` is a governance-core path; needs its own review |
| Bound transitive closure amplification for all changes (e.g. #337 requires 14 docs) | Reduces filler doc edits generally | LATER |
| Auto-merge Dependabot PRs that pass | Less manual work | REJECT — contradicts `automatic_merge_authorized: false` and Human merge authority |

## Risks

- A future Dependabot format (e.g. comment `# v4.38.3-rc1`, hash-pinned requirements) falls outside the shape and stays blocked; acceptable, fail-closed.
- `-U0` parsing must handle multiple hunks per file and files without trailing newline; covered by fixtures.
- After this lands, Dependabot PRs still need rebase onto the new `main` and must pass every other gate; #337/#339 additionally hit the matrix requirement.

## Proposed Implementation Order

1. Add fixtures that reproduce today's failures for #338 / #262 shapes.
2. Implement predicate + policy validation in `dependency_impact.py`.
3. Wire `documentation_impact`, placement and sync consumers; Step Summary rendering.
4. Positive / negative lifecycle tests; replay real PR heads #338 and #262 locally.
5. Documentation closure, Core Change Test Matrix, `capability_registry.py check`, full local Gate.
6. Commit to `claude/deps-docs-impact-1d4bcd`. Push / PR only after the Git Publish Approval Gate and a fresh Human confirmation.

## Approval

Status: APPROVED
Approved by: User (relayed verbatim by the parent session local_649ad323)
Approved at: 2026-10-20 (Asia/Taipei)
Approval record: 「核准這個 Core Change 方案，高風險類別採用選項 A（全部豁免文件要求，並標記需要人工審查）。請子 session 進入階段二實作。」 Option A selected for HIGH-risk classes. Push / PR remain subject to the Git Publish Approval Gate and a fresh Human confirmation.
Proposal fingerprint: sha256:92f9e923667f66c5b9975c699a042fca78fac6d9131157081aa980e01210f1fb (proposal bytes preceding this Approval section)
Scope fingerprint: In scope / Out of scope sections as approved; recomputed against the final diff before commit.
