# System Improvement Review: Claude Code Publication Command Compatibility (Dev Friction PR1)

Appropriateness: Appropriate. A Hook harness reproduced three false or unhelpful denials: literal backticks/`$` in a quoted-heredoc PR body were treated as expansions, every PR creation lacked operation-bound scan evidence after Prepare, and a chained push/PR returned `INTERNAL_DIAGNOSTIC_GAP`. Other denials were correct but did not name the supported form.

User problem: Claude Code is denied while committing, pushing or opening PRs and retries guessed variants, which costs turns and can look like guard evasion.

Proposed solution: Reuse the existing NUL-marked Shell classification for personal publication, store PR-bound evidence from the same Prepare scan, lengthen the evidence TTL to 30 minutes, and return static bilingual recipes.

Existing coverage: `shell_commands(mark_dynamic=True)` already powers commit literal handling; Prepare already scans the exact candidate; diagnostics already carry `detail_code`, `next_step` and `next_step_zh`.

Reuse / extension candidates: Extend `publication_commands.py`, `publication_authority.py`, `governance_guard.py`, `publication_planning.py`, `publication_scan_evidence.py`, existing publication tests and Scenario 261.

Lower-layer alternative: A Claude-only instruction workaround (always use `--body-file`) would not fix PR evidence binding or the diagnostic gap, so the shared guard must change.

Context / token cost: One short adapter section; no new Turn Context or provider.

Security / reliability: Secret, PII and content scans, one protected operation per call, exact candidate/target/policy binding, Human merge confirmation and the `--admin` prohibition are unchanged. Real expansions stay denied. Diagnostics never echo input.

Backward compatibility: New keyword arguments default to previous behavior; JSON envelopes are unchanged; only recovery text and detail codes improve.

Scenario / test impact: Scenario 261; `tests/test_publication_authority.py`, `tests/test_publication_planning.py`, `tests/test_publication_scan_evidence.py`.

Human docs impact: User Guide, Security Assurance, Technology Guide, Harness and Architecture TTL wording.

Agent docs impact: Claude Code adapter standard publication recipe; Harness Protocol TTL wording.

Architecture diagram impact: N/A. No trust boundary or authority flow changes.

Constitution impact: NO.

Why: Human authority, approval semantics and release permissions are unchanged.

Recommended AIPS solution: Implement the PR1 scope as proposed.

Additional optimization candidates: NOW — classify multiple protected operations explicitly. LATER — Prepare-stored evidence for planned merges, and `aips publish ship` (PR7). REJECT — accepting bare-branch pushes, inferring PR repository/head/base, or unquoted heredocs.

Expected scope: Shared parser/guard/Prepare, focused tests, Scenario 261 and localized documentation.

Risks: A missed expansion form would be a false allow; it is mitigated by NUL marking, regression tests and fail-closed parsing. Planned merges remain denied in the Claude Code Hook for lack of merge-bound evidence.
