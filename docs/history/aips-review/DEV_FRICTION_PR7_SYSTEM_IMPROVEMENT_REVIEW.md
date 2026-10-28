# System Improvement Review: `aips publish ship` and Merge-Bound Scan Evidence (Dev Friction PR7)

Appropriateness: Appropriate. Personal publication needed three Hook round trips (Prepare, exact push, Prepare, PR create), each with its own exact-candidate scan, and a standalone merge was always denied because Prepare stored no merge-bound evidence (found in the PR1 review).

User problem: Agents hit multiple denials and retries to push and open one PR, and a merge the user asked for could not pass the Hook at all.

Proposed solution: One `aips publish ship` command whose Hook validation and CLI chain share one parser, one candidate observation and one scan; child git/gh calls are re-validated before they run. Prepare stores evidence for the merge operation, using the same scope that validates the merge checks.

Existing coverage: `publication_authority.action` already validates the exact push and PR scopes; `publication_scan_evidence` already binds evidence to every scope field; `publication_planning.prepare` already plans the PR and merge commands; the Hook already classifies protected operations and denies unknown forms.

Reuse / extension candidates: Extend `publication_commands.py` (classifier), `publication_planning.py` (merge evidence), `governance_guard.py` (protected operation), `publication_authority.py` (diagnostics), `publish_preflight.py` (CLI), and the existing publication test suites.

Lower-layer alternative: A documented three-command workflow with a longer evidence TTL would not remove the repeated scans or the merge denial; a Claude-only instruction would not bind the child commands to the Hook. The shared Hook and CLI chain must change.

Context / token cost: One preferred sentence block in the Claude adapter; one help line. No new Turn Context, provider or runtime.

Security / reliability: Secret, PII and content scans run once for the exact candidate with the same policy; push stays exact-SHA with no force flags; PR head and base must match the candidate branch and the remote default branch; merge keeps the head pin, enabled-method, `--admin`/`--delete-branch` prohibition and Human confirmation. Child output is never echoed. High assurance denies ship.

Backward compatibility: Individual Prepare, push and PR commands are unchanged. The only Prepare change adds merge evidence. The merge denial message now names `aips publish ship` for push and PR and keeps `aips publish prepare` for merge.

Scenario / test impact: Scenario 273 (new); `tests/test_publication_ship.py` (new); `tests/test_publication_planning.py` (two merge mocks now return a real merge scope); `tests/evidence/governance_command_guard.py` (ship classification cases).

Human docs impact: None beyond the required minimal publication sentences; the whole-branch documentation closure stays with the main agent.

Agent docs impact: Claude Code adapter standard publication recipe and the `aips publish` help line.

Architecture diagram impact: N/A for this change; the chain is a CLI sequence inside the existing publication authority, with no new trust boundary.

Constitution impact: NO.

Why: Human authority, approval semantics and release permissions are unchanged. Publication still needs the same scan, binding and confirmation.

Recommended AIPS solution: Implement the PR7 scope as proposed.

Additional optimization candidates: NOW — none beyond this scope. LATER — classifying interpreter code that imports the publication CLI (`python -c`), which is a Hook-wide limitation. REJECT — `--force` in ship, merge without human confirmation, a second command form for push, and reusing evidence across a changed remote tip.

Expected scope: Shared classifier and Hook dispatch, one new publication module, the Prepare merge evidence line, the CLI subcommand, focused tests, Scenario 273 and minimal adapter and help documentation.

Risks: A child command outside the CLI path is the main risk; it is mitigated by building child argv only in `publication_ship.py`, denying any second protected command, and re-validating each child. A rerun after PR-create failure rescans once because the remote tip changed.
