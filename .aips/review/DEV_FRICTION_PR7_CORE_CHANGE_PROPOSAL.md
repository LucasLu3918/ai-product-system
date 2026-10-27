# Core Change Proposal: `aips publish ship` and Merge-Bound Scan Evidence (Dev Friction PR7)

## Purpose

Replace the three-step personal publication sequence (Prepare, exact push, PR create), which costs several Hook denials and retries, with one `aips publish ship` command that scans the exact candidate once. Also make a standalone personal-mode `gh pr merge` reachable: Prepare stores merge-bound evidence, so the Hook can accept the merge only when the same checks pass and human confirmation still applies.

## Why this is a core/large change

It adds a protected publication operation (`publish_ship`), a new CLI chain that runs `git push` and `gh pr create` as child processes, and a new Hook classification path for the `aips` CLI and `publish_preflight.py ship`. A false allow could publish an unscanned or stale candidate; a false deny keeps the friction this PR removes.

## Measured Baseline

| Form | Before PR7 | After PR7 |
|---|---|---|
| Prepare, then exact push, then Prepare, then `gh pr create` | three or more Hook round trips; each push and PR needs its own Prepare and exact-candidate scan | one `aips publish ship` Bash command; the Hook validates it once and the CLI runs one scan |
| `aips publish ship ...` | command does not exist | allowed only when the single supported form validates; any extra option, dynamic value, chained protected command or high-assurance mode is denied |
| `python scripts/publish_preflight.py ship ...` | not classified | classified as `publish_ship` (same validation) |
| standalone `gh pr merge <PR> --<method> --match-head-commit <sha>` after Prepare | always denied `PUBLICATION_SCAN_EVIDENCE_REQUIRED`: Prepare stored only push-bound evidence | allowed by the Hook only with merge-bound evidence for the same candidate; human confirmation (`ask`) unchanged |
| merge after a candidate change | denied | still denied: evidence binding includes candidate, target, remote OID, diff and policy |

## Proposed Scope

### In scope

- `aips publish ship --title <title> --body-file <file> --base <default-branch> [--head <branch>]`: strict literal grammar (one value per flag, no `=` form, no other options). Steps: one candidate scan (reused only when fresh evidence exists for the exact push scope), `git push origin <full-candidate-sha>:refs/heads/<branch>` (same personal-mode argv that Prepare plans), then `gh pr create --repo --head --base --title --body-file`. Each child is re-observed and re-validated against the same candidate, scan evidence and body digest immediately before it runs. Any step failure stops the chain with `SHIP_PUSH_FAILED` or `SHIP_PR_CREATE_FAILED` and a bilingual recipe. A rerun skips a completed push and reports an existing PR.
- Hook (`scripts/governance_guard.py`): `publish_ship` joins the protected operations. Personal mode validates the ship invocation (exact candidate, push scope, remote tip, policy digest, scan evidence, PR base and head). High-assurance mode denies with `ASSURANCE_MODE_BLOCKED`. Success records the candidate, target ref, remote OID, policy digest and scan binding digest.
- Shared classifier `publish_ship_arguments` in `scripts/publication_commands.py`, used by both the Hook and the CLI; a dynamic word in the `aips publish` subcommand position denies with `DYNAMIC_SUBCOMMAND`.
- Prepare (`scripts/publication_planning.py`): for `gh pr merge`, store scan evidence bound to the merge scope returned by the same `action` call that validates the merge checks (head SHA pin, enabled method, no `--admin`/`--delete-branch`, required checks). No change to the merge checks, the human-confirmation path or the `ask` decision.
- Denial recipes: `SHIP_FORM_UNSUPPORTED` names the single command in English and Traditional Chinese; `PUBLICATION_SCAN_EVIDENCE_REQUIRED` names `aips publish ship` for push and PR and `aips publish prepare` for merge.
- Tests, Scenario 273 and its coverage entry, Claude adapter recipe (one preferred sentence block), and the `aips publish` help line.

### Out of scope

- Any weakening of secret, PII or content scanning, of exact SHA binding, of Human merge confirmation, or of the `--admin`/`--delete-branch` prohibition.
- Email allowlisting; new network endpoints beyond the existing `gh` and `git` calls.
- Automatic merge without an explicit user request; any force push (`--force`, `--force-with-lease`) in ship.
- Classifying arbitrary interpreter code (`python -c ...`) as publication; this remains a documented limitation of the Hook.
- Documentation closure for the whole integration branch (main agent) and the Core Change Test Matrix file (not edited here).

## Expected Files / Modules

- New: `scripts/publication_ship.py`, `tests/test_publication_ship.py`, `tests/scenarios/273-publish-ship-single-command.md`, this proposal and the review.
- Changed: `scripts/governance_guard.py`, `scripts/publication_commands.py`, `scripts/publication_planning.py`, `scripts/publication_authority.py` (diagnostics only), `scripts/publish_preflight.py`, `scripts/aips_cli/help.sh`, `tests/test_publication_planning.py` (two merge mocks now return a real merge scope), `tests/evidence/governance_command_guard.py`, `tests/scenario_coverage.yaml`, `harness/adapters/claude-code/CLAUDE.md`.

## Impact

### Architecture / Contracts

A new protected operation `publish_ship` joins `PROTECTED`, and the Hook gains one classification rule for `aips publish ship` and `publish_preflight.py ship`. The CLI is the only component that spawns `git push` and `gh pr create` for this chain; the Hook never sees those children. This is not a new trust boundary: each child runs the same validation that the standalone Hook path uses, immediately before it executes.

### Data / Migration

No persistent product data. Scan evidence records are the existing short-lived, private cache files; `ship` writes them with the same `store` function and TTL.

### Security / Reliability

- One protected operation per Hook invocation is preserved for the agent: `aips publish ship` is one Bash command, and any chained or additional protected command is denied.
- The one scan has the same strength as the existing exact-candidate scan (`scan_candidate` over the candidate and history with the same policy). Evidence is reused only when every binding field (repository, worktree, base, candidate, operation, target, remote OID, diff, policy and scanner digest) matches; forged or stale evidence is ignored.
- Each child is re-observed before execution. A candidate change stops with `CANDIDATE_CHANGED`; a remote tip change requires a fresh scan (`PUBLICATION_SCAN_EVIDENCE_REQUIRED`); a changed body stops before PR create.
- Merge evidence is bound to the merge scope (candidate = PR head pinned by `--match-head-commit`, target `refs/heads/<base>`, base tip, diff and policy). It removes only the evidence-missing denial; the head-pin, method, `--admin`/`--delete-branch`, required-check and human-confirmation checks run unchanged in `action()` and the Hook's `ask` path.
- Child output is never echoed; only return codes and bounded diagnostics leave `publication_ship.py`.
- High-assurance mode denies ship with `ASSURANCE_MODE_BLOCKED` because the approval-record workflow has no `publish_ship` operation.

### Compatibility / Rollback

Individual Prepare, push and PR commands keep their behavior; the only changed Prepare behavior is the additional merge evidence. Rollback: revert the commit; the new module and Hook classification disappear, and stored merge evidence expires within 30 minutes.

### Tests / Validation

`tests/test_publication_ship.py` (21 tests: grammar, classifier, one scan and chain order, rerun, child failures, scan block, forged evidence, candidate and remote-tip changes between scan and child, high assurance, Hook binding and denials, merge evidence before and after Prepare and after a candidate change, CLI reachability with no network). Existing publication suites run twice; governance command evidence; repository validators; capability registry check. All GitHub interactions are mocked; the local bare remote is the only Git endpoint.

### Secret / Credential Impact

Secrets required: NO. No token is read or written; `GIT_TERMINAL_PROMPT=0` and `GH_PROMPT_DISABLED=1` prevent interactive credential prompts in child processes.

## Risks

- A child command could be invoked outside the CLI path. Mitigation: the child argv is built inside `publication_ship.py` only; the Hook denies any second protected command; the CLI re-validates before each child.
- `python -c` or other interpreter code that imports `publish_preflight` is not classified (existing class of limitation, unchanged).
- Rerun after a failed PR create rescans once because the remote tip has changed; this costs one scan and does not weaken binding.
- The ship chain depends on GitHub REST evidence through `gh pr list`/`gh pr create`; a permission failure stops the chain with a repair recipe.

## Recommendation

Implement the scoped `ship` chain and the Prepare merge-evidence fix as a single PR7 change inside the existing publication authority; do not add a new guard, relax a binding or change the human-confirmation path.

## Approval

Status: APPROVED
Approved by: Human (explicit task instruction)
Approved at: 2026-10-26
Approval record: The user approved the full AIPS dev-friction plan, including decision D4 (`aips publish ship` is in scope and is itself a protected publication operation), and asked to execute the plan. This approval covers exactly the PR7 scope above.
Proposal fingerprint: computed from the committed proposal in the candidate matrix.
Scope fingerprint: bound to the actual changed-file set in the candidate matrix.
