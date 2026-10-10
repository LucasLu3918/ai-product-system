# System Improvement Review: Claude Shell Command Substitutions

Appropriateness: Appropriate. The measured failure is a false denial caused by assuming fixed Git/GitHub command-token positions; heredoc expansion handling is another confirmed parser limitation.

User problem: Claude sometimes spends extra tool calls splitting safe Shell work because AIPS returns a generic unsupported-syntax denial.

Proposed solution: Improve the existing bounded Shell AST parser and shared runtime guard; add precise reason codes and cover unquoted heredoc substitutions.

Existing coverage: `publication_commands.py` already parses Bash ASTs and recursively visits nested command substitutions. Existing tests cover strings, quoted heredocs, executable substitutions and fail-closed dynamic commands.

Reuse / extension candidates: Extend `publication_commands.py`, `governance_guard.py`, `tests/test_publication_authority.py` and Scenario 097. Reuse Claude/Gemini hook envelopes and current publication authority.

Lower-layer alternative: No project-only workaround is appropriate because the parser and hook are shared AIPS behavior. A caller can use a literal argument after `--` as a temporary workaround, but it does not resolve general safe argument classification.

Context / token cost: No new turn context or provider. Parser traversal remains bounded to submitted command text; no command execution is introduced.

Security / reliability: Preserve fail-closed behavior for malformed input, dynamic executable/subcommand/context and unbindable publication arguments. Do not log raw command payloads.

Backward compatibility: Preserve `shell_commands()` return shape, public function locations and hook JSON envelopes; reason text becomes clearer. Existing unsupported heredoc uses become supported only when AST inspection succeeds.

Scenario / test impact: Scenario 097, publication authority unit/lifecycle tests, documentation placement, repository validator, secret scan and exact-candidate Integration Gate.

Human docs impact: Security Assurance, User Guide, Technology Guide, Architecture Overview, Architecture and Maintenance/Conformance sections.

Agent docs impact: Runtime Policy Enforcement, Orchestrator and Deterministic Scheduler guidance.

Architecture diagram impact: N/A. The trust boundary and authorization flow do not change.

Constitution impact: NO.

Why: No change to Human authority, approval semantics, scope integrity or release permissions.

Recommended AIPS solution: Implement the bounded AST extension, recursive heredoc substitution classification, actionable sanitized reason codes and regression/documentation closure.

Additional optimization candidates: NOW — stable denial codes with generic recovery hints, included because the user approved all proposed items. LATER — cache parsed AST nodes across multiple policy consumers within one hook invocation only if profiling shows meaningful cost. REJECT — execute substitutions in the hook or broadly allow dynamic publication arguments.

Expected scope: Shared parser/guard, one existing regression module/scenario, canonical security/runtime/user/maintenance/architecture/conformance docs and exact-candidate Core artifacts.

Risks: Incorrect quoting semantics could create false negatives; ambiguous forms must remain denied. Personal mode's writable-origin limitation and Codex ADVISORY capability are unchanged.
