# Core Change Proposal: Documentation Sync Dot-Prefix Normalization

## Purpose

`scripts/documentation_sync.py::evaluate_changes` normalizes changed paths with `str(x).strip().lstrip("./")`. `str.lstrip` removes a leading *character set*, not a prefix, so `.github/workflows/validate.yml` becomes `github/workflows/validate.yml`. Every trigger in `config/documentation-sync.yaml` that starts with `.github/` therefore never matches, and the documentation consistency check in `scripts/repository_preflight.py` (run by `.github/workflows/validate.yml` and by `scripts/publish_preflight.py`) silently passes workflow changes that the configuration says require documentation review.

Dead triggers today (main `172128e8`):

| Config entry | `.github/**` triggers |
|---|---|
| `technology_guide` | `.github/workflows/**` |
| `maintenance-planning` | `.github/workflows/branch-hygiene.yml` |
| `maintenance-reliability` | `.github/workflows/maintenance-reliability.yml` |
| `evolution-radar` | `evolution-radar.yml`, `evolution-decision.yml`, `evolution-effectiveness.yml` |
| `project-intelligence` | `retrieval-semantic-trial.yml` |
| `execution-isolation` | `e2b-sandbox-verification.yml` |
| `publication-preflight` | `validate.yml` |
| `documentation-platform` | `docs-site.yml` |

## Why this is a core/large change

It changes the behavior of a required repository gate (Documentation consistency inside `repository_preflight`), making it stricter for every future workflow change. It was explicitly split out of the Dependabot preflight/pin-sync Core Change (`DEPENDABOT_PREFLIGHT_PIN_SYNC_CORE_CHANGE_PROPOSAL.md`, PR #354) for independent review.

## Proposed Scope

### In scope

- Replace `.lstrip("./")` in `evaluate_changes` with removal of a single leading `./` (`.removeprefix("./")`), keeping all other matching semantics unchanged.
- Regression contracts in `tests/validation/documentation_sync_contracts.py`:
  - `.github/workflows/<x>.yml` triggers the Technology Guide and the matching rule;
  - `./scripts/x.py` still normalizes to `scripts/x.py`;
  - other dot-directories (`.aips/…`, `.claude/…`) are not mangled.
- Documentation sync required by this change itself (simulated with the fixed evaluator): `docs/human/TECHNOLOGY_GUIDE.md`, `docs/human/DOCUMENTATION_SYNC.md`, `docs/human/DOCUMENTATION_MAP.md`, `orchestration/DOCUMENTATION_SYNC.md` — a short note that `.github/**` triggers are now enforced.
- One scenario under `tests/scenarios/` (next free number at implementation time; currently 267) plus the Core Change test matrix.
  - Implementation note (smaller than proposed): Scenario 221 is the only scenario covering Documentation Sync and already owns `evaluate_candidate`, so the normalization behavior is added there instead of registering a new Scenario 267.

### Out of scope

- Rewording or narrowing any trigger in `config/documentation-sync.yaml` (e.g. whether `technology_guide` should keep `.github/workflows/**`). Recommended as a separate decision if the new strictness proves noisy.
- The same `lstrip("./")` pattern in `scripts/aips_common/patterns.py` (`slash_lstrip` mode) and `scripts/visual_profile.py::normalize_path`. Their callers are visual-profile only and no current pattern starts with `.`; listed as a follow-up.
- Any change to `evaluate_candidate` / the pure-dependency exemption (owned by PR #354).

## Precondition / Ordering

`documentation_sync.evaluate_candidate` (the pure-dependency exemption wired into `repository_preflight`) is **not on main yet**; it exists only in open PR #354 (`claude/preflight-pin-sync-f07b9a`, head `480ece57`). Main's `repository_preflight` still calls `evaluate_changes` directly.

This fix must be based on, and merged after, #354. Merging it first would newly block all four open Dependabot GitHub Actions PRs (see below).

## Impact

### Measured: open PRs (heads fetched 2026-10-20, diff `origin/main...head`, config from #354 head)

| PR | Workflow files | Today (`lstrip`) | Fixed `evaluate_changes` alone | Fixed + `evaluate_candidate` (#354) |
|---|---|---|---|---|
| #340 codex-action 1.13 (Dependabot) | evolution-decision, evolution-radar | 0 | 3 (Tech Guide, evolution-radar human+agent) | `PURE_DEPENDENCY_UPDATE`, 0 |
| #339 upload-artifact 7.0.2 (Dependabot) | 11 workflows | 0 | 9 (Tech Guide, maintenance-planning, maintenance-reliability, execution-isolation, publication-preflight) | `PURE_DEPENDENCY_UPDATE`, 0 |
| #337 setup-node 7.1.0 (Dependabot) | docs-site, validate | 0 | 5 (Tech Guide, publication-preflight, documentation-platform) | `PURE_DEPENDENCY_UPDATE`, 0 |
| #259 scorecard-action (Dependabot) | scorecard | 0 | 1 (Tech Guide) | `PURE_DEPENDENCY_UPDATE`, 0 |
| #263 #262 #261 #260 #168 (Dependabot pip) | none | unchanged | unchanged | `PURE_DEPENDENCY_UPDATE`, 0 |
| #354 preflight pin sync | none | 0 | 0 | 0 |
| #318 Matt Pocock skills | none | 4 (pre-existing, unrelated) | 4 | 4 |
| #283–#288 Plan25 docs | none | 0 | 0 | 0 |

Conclusion: with #354 merged first, no open PR's documentation-sync result changes. Dependabot workflow PRs stay exempt because the exemption runs before `evaluate_changes`. (#339/#337 still face the separate `matrix_required` issue on `validate.yml`, unrelated to this change.)

### Measured: history (last 200 first-parent commits on main touching `.github/**`, evaluated against today's config)

Only four merges would have produced additional errors: #338 (Dependabot, exempt under #354), #172 (one extra project-intelligence agent doc), #147 and #149 (publication-preflight docs). Almost all human workflow changes already co-modified the required docs, so the expected friction for future human PRs is low; the main new requirement is updating `docs/human/TECHNOLOGY_GUIDE.md` when only a workflow file changes.

### Architecture / Contracts

One-line normalization change in `evaluate_changes`; all consumers (`repository_preflight`, the CLI, `evaluate_candidate`, contracts) inherit it. No config or schema change.

### Data / Migration

None.

### Security / Reliability

Strictly fail-closed direction: a check that was silently skipped starts enforcing. No new bypass. The pure-dependency exemption remains the only exemption path and is unchanged.

### Compatibility / Rollback

Future human PRs that touch only `.github/workflows/**` will need documentation updates. Rollback is reverting the one line.

### Tests / Validation

- New contracts above; existing `validation.documentation_sync_contracts` must still pass.
- Replay `repository_preflight --base origin/main --head <head>` for #340, #339, #337, #259 heads on top of the candidate (expect PASS via exemption) and a synthetic human workflow-only commit (expect Technology Guide failure).
- Full local Gate (`publish_preflight.py run`, core) before asking for push approval.

### Secret / Credential Impact

Secrets required: NO.

## Risks

- New friction for workflow-only human changes (Technology Guide). Mitigation: decide trigger scope separately if noisy.
- If #354 is changed so the exemption no longer covers a Dependabot PR, that PR will now fail documentation sync instead of passing silently — the intended direction.

## Recommendation

Apply the prefix-only normalization with regression contracts, based on #354 and merged after it. Leave trigger scope and the `visual_profile` / `patterns.slash_lstrip` occurrences to follow-ups.

## Proposed Implementation Order

1. Wait for #354 to merge (or base on its head if the user prefers stacking).
2. Change normalization; add contracts and scenario.
3. Synchronize the four documents and the Core Change matrix.
4. Replay the PR heads and the synthetic workflow-only case; run the full local Gate.
5. Ask the user before push / PR.

## Approval

Status: APPROVED
Approved by: Human (direct instruction in session)
Approved at: 2026-10-20
Approval record: 「核准此提案，等 #354 合併後再以 main 為基底實作，push 前再問我。」 Implementation is deferred until PR #354 is merged; the branch is then rebased onto that main. Push / PR still require a separate Git Publish Approval.
Proposal fingerprint: computed from the committed proposal in the candidate matrix.
Scope fingerprint: bound to the actual changed-file set in the candidate matrix.
