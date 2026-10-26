# System Improvement Review: Installed System and Profile Write Protection, Preflight Degradation (Dev Friction PR3)

Appropriateness: Appropriate. An agent edited the installed AIPS checkout in place, and every later `aips system preflight` or `aips update` refused until the user cleaned it up, which stalled unrelated creative work. Only the guard and the preflight path need changes; the installed copy is not a development workspace.

User problem: Agent edits in the installed system break preflight and update, and the user has to reconstruct a clean tree by hand.

Proposed solution: Extend the existing PreToolUse guard to file-edit tools and common Shell write forms that target the installed checkout or profile settings, deny with a stable reason code, and make preflight skip (not fail) on a dirty installed checkout while the explicit `aips update` keeps refusing.

Existing coverage: The guard already fails closed with static diagnostics, the installer already writes the managed guard group, and `update_system` already has a clean-tree check.

Reuse / extension candidates: `scripts/governance_guard.py` (deny envelope and diagnostics), `scripts/manage_runtime_adapter.py` (managed group), `scripts/aips_cli/maintenance.sh` (update and preflight).

Lower-layer alternative: Filesystem permissions on the installed checkout (read-only mode or a separate user). Not chosen here because it changes the installation model and breaks the human `aips update`. Documented as a possible later hardening step.

Context / token cost: Denials add a static, bounded diagnostic; no Turn Context change.

Security / reliability: The change only adds denials for protected writes and never widens write authority. Publication, scanning and merge confirmation are untouched. Explicit `aips update` still refuses without modifying the tree. Bash coverage is best-effort and documented as such.

Backward compatibility: The Claude matcher now includes file-edit tools for newly installed or refreshed settings only. Preflight output changes on a dirty checkout (warning instead of stop).

Scenario / test impact: `tests/test_protected_path_guard.py` and `tests/test_system_preflight_degradation.py` are new; the existing publication and governance guard suites stay unchanged.

Human docs impact: HARNESS, SECURITY_ASSURANCE, INSTALLATION. Agent docs impact: Claude Code adapter CLAUDE.md and HARNESS_PROTOCOL.

Architecture diagram impact: N/A. No trust boundary or authority flow changes.

Constitution impact: NO.

Why: Human authority and approval semantics are unchanged; agents gain no new write path.

Recommended AIPS solution: Implement the PR3 scope as proposed; document the Bash limits; treat filesystem-level protection as a separate later decision.

Additional optimization candidates: NOW — none beyond the scope. LATER — read-only permissions on the installed checkout; classify interpreter-based writes; PR10 profile file creation may need its path added to the protected set (already reserved as `profile.yaml`). REJECT — claiming complete enforcement for Bash, or silently discarding local changes during preflight.

Expected scope: Guard, installer template, one maintenance shell function, two test files, five docs.

Risks: A false deny for an unusual shell form; a determined agent can still write through an interpreter. Both are documented in the proposal and in the docs.
