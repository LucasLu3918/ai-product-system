# System Improvement Review — Skill Incubation

Appropriateness: Appropriate. Skill index and reuse review show reusable gaps in frontend implementation, systematic debugging, product LLM integration, browser E2E, observability, live-data migration, dependency upgrades, ADRs and game development.

User problem: AIPS has reusable guidance gaps despite having the matching engineering, design, product, testing, database and operations Capabilities.

Proposed solution: Add narrow Skills, extend adjacent Skills where reuse is coherent, update routing scenarios and add one stable browser-game reference.

Existing coverage: Existing UX and visual-review Skills do not govern frontend implementation; TDD does not cover browser journeys; incident-response handles incidents rather than pre-launch signals; data-modeling is not a live migration method; performance-profiling and product-research provide suitable extension points.

Reuse / extension candidates: Extend ux-web-design for page audits, performance-profiling for real-time frame budgets, and product-research for playtesting. New methods remain separate from existing incident, API, testing, security and architecture Skills.

Lower-layer alternative: Project Intelligence could hold project-specific conventions, but these are reusable cross-project methods and belong in canonical Skills. Engine and platform details remain references.

Context / token cost: Skills are loaded on demand; no bootstrap payload is added. Registry entries have low or medium estimated cost and model tiers follow each Skill's risk.

Security / reliability: Include untrusted-input and least-privilege rules for LLM tools, secret-safe observability, migration recovery, dependency provenance, consented research and legal-review boundaries for paid random rewards.

Backward compatibility: Additive SKILL.md files and generated compatible v1 INDEX; preserve existing IDs and consumers. No runtime interface or data migration changes.

Scenario / test impact: Add Scenarios 241–256 as manual semantic expectations; keep Skill Index lifecycle evidence deterministic and separate. Run documentation placement, scenario conformance, full repository validation and exact-candidate Integration Gate.

Human docs impact: Update Technology Guide, Architecture Overview, Maintenance guidance and generated Conformance summary. No new user-facing product workflow.

Agent docs impact: Skills remain canonical Agent surfaces; update documentation placement and Skill Index only. No orchestration or runtime policy changes.

Architecture diagram impact: Existing Skill metadata → generator → INDEX → implementation flow remains accurate; update adjacent explanation and record Mermaid/SVG topology as N/A.

Constitution impact: NO.
Why: No Human authority, safety, policy, privacy, scope, or approval semantics are changed.

Recommended AIPS solution: Add 13 admitted Skills and extend three existing Skills; do not add a game Capability or Role. Do not add multiplayer-netcode unless a real-time multiplayer product requirement appears. Keep native web DOM/SVG details in a reference.

Additional optimization candidates: None recommended NOW.

Expected scope: Skill sources and index; 16 scenarios and registry; native web game reference; documentation placement and required Human docs; active Core review artifacts.

Risks: Trigger overlap and quality drift are controlled through explicit non-triggers, companion links and manual scenarios. Manual scenarios do not establish model routing quality. Real-game implementation/player testing remains a later project validation milestone.

Approval: The user explicitly requested implementation of all recommendations in the attached plan.
