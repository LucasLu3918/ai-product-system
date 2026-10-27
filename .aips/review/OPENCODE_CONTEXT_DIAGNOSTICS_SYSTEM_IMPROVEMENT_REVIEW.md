# System Improvement Review: OpenCode Context Overflow Diagnostics

Appropriateness: **APPROPRIATE**. The compact projection already fails closed at its 12,000-byte boundary, but its generic message does not show what exceeded the limit or how to recover.

User problem: OpenCode users can receive “Turn Context unavailable” without knowing whether context generation failed or compaction itself exceeded the size limit.

Proposed solution: Preserve the existing compact projection and write-denial boundary. When the projection remains oversized, return a stable reason code, original and projected byte counts, up to three fixed section names and serialized sizes, and safe inspection/refresh commands. Expose only bounded metadata through the existing privacy-filtered trace.

Existing coverage: The OpenCode plugin already caps Context at 12,000 UTF-8 bytes and denies supported project writes when Context is unavailable. `aips harness trace` already uses an allowlist. Neither identifies irreducible projection overflow or provides targeted recovery guidance.

Reuse / extension candidates: Extend the existing OpenCode Context compaction path and trace allowlist; do not add a new Role, Skill, Capability, command, or approval gate.

Lower-layer alternative: A documentation-only workaround cannot distinguish runtime failures from the deterministic projection-size failure. A small pure helper beside the existing adapter is the narrowest reusable seam for byte sizing, failure formatting and focused lifecycle evidence.

Context / token cost: No bootstrap or successful-turn cost. The diagnostic is computed only when the source is oversized; only bounded numeric metadata and fixed section names are added to the private trace.

Security / reliability: Preserve fail-closed behavior for both Context delivery and supported native file writes when the projection is irreducibly oversized. Do not expose section values, prompts, raw CLI output, credentials or paths. The trace reader rejects unknown names, excess entries and out-of-bound byte values. This changes diagnostics and restores the intended deny-on-unavailable Context invariant; it does not expand Host-hook coverage.

Backward compatibility: Additive failure text and trace fields. Successful Context JSON, 12,000-byte limit, native permissions and existing OpenCode version routing remain unchanged. No migration or persistent state change.

Scenario / test impact: Extend Scenario 235 and the owning OpenCode lifecycle and static contract to cover compacted success, irreducible overflow, safe recovery text, trace allowlisting and write denial.

Human docs impact: Update the OpenCode compatibility guide, Harness user guide, Scenario 235, scenario coverage and Unreleased changelog.

Agent docs impact: Update OpenCode compatibility and system-improvement review artifacts; no bootstrap protocol or global authority changes.

Architecture diagram impact: **N/A**. The existing adapter flow, state ownership and trust boundaries do not change.

Constitution impact: **NO**. Human authority, project precedence, safety boundaries and publication semantics remain unchanged.

Recommended AIPS solution: Implement the bounded diagnostic in the existing OpenCode adapter and retain the current deny-until-restored behavior.

Additional optimization candidates: None added to this scope.

Expected scope: A focused ESM helper, OpenCode plugin integration, privacy-filtered trace schema, lifecycle/contract evidence, Scenario 235, mapped human documentation, changelog, Core Change Proposal and candidate-bound Test Matrix.

Risks: Section sizes describe the compact projection, not a complete attribution of the original manifest. Context unavailable for CLI, JSON or session failures remains distinguishable from this specific compaction-over-budget reason. Native Host execution remains separately verified and is not upgraded by fixture evidence.

Approval: The user selected “修正 OpenCode Context 超限診斷與排除（建議）” for implementation in this task. Remote publication and merge remain subject to the exact-candidate Git Publish Approval Gate and native GitHub checks.
