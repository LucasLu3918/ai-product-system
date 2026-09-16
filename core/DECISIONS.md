# Consolidated Architecture Decisions

This file is the compact record of accepted design decisions. Use a new ADR only for future material architecture changes that need their own rationale/history.

| Topic | Accepted decision |
|---|---|
| Constitution | Minimal protected layer for human authority, truth, safety, stop-the-line, scope integrity and high-risk approval; lower layers cannot override it |
| System self-improvement | Every user suggestion about this system is reviewed for appropriateness, duplication, simplification, optimization, compatibility and Constitution impact before implementation |
| Constitutional change | Requires affected-Article/risk analysis and a second explicit Constitutional Approval; prefer lower-layer change |
| Core change approval | Large/core changes are proposal-first; semantic impact > file count; material scope drift requires re-approval |
| Git publish approval | Before remote branch/ref publication, show file list, feature summary, validation evidence and atomic commit plan; wait for explicit approval |
| Atomic commits | Group commits by logical capability, reviewability and revertability; never split merely by file |
| Agent model | Role + Capability/Skill + Context + Task |
| Human authority | Protected Human Authority |
| Context loading | Hierarchical progressive context resolution |
| Autonomy | Governed Autonomy |
| Preflight | Material recommendation/unknown/risk/capability-gap check before implementation |
| System update | Before mutating implementation, run safe Update Preflight: clean `main`, fetch, `git pull --ff-only`, no auto merge/rebase |
| Major upgrades | Explicit review/approval required before applying a new MAJOR system version |
| System provenance | Record exact system version + commit in target project `.ai/SYSTEM.yaml` |
| Primary planning | Authoritative product/project planning must be physically persisted; ask for workspace when none is specified |
| Planning completeness | Reproducible Planning Package contains product, experience, visual/key visual, architecture, API/contract when applicable, implementation readiness, and decisions/assumptions |
| Planning approval | Gate 1 approves the persisted Planning Package; Gate 2 separately approves Initial Implementation Items + Recommended Implementation Flow before implementation |
| Existing projects | Inspect first; discover scoped instructions; establish change boundary; avoid unrelated refactors |
| Project precedence | Current explicit user decision > scoped project instructions/decisions > project skills > global skills, under system safety guardrails |
| Scoped instructions | Nearest applicable `AGENTS.md` wins over broader project scope |
| Overrides | One-task overrides remain temporary unless the user approves a permanent policy change |
| Testing | TDD by default for testable behavior; appropriate strategy elsewhere; characterization tests for risky untested legacy behavior |
| Review | Author and final reviewer are separate for material changes |
| Work routing | Intent-based Work Modes; greenfield/brownfield is project state |
| Skills | Small, reusable, independently loadable leaf knowledge; skills have expertise but no governance authority |
| Capability gaps | Reuse skill → new skill → new capability → new role; stop before guessing |
| Deterministic automation | Prefer existing deterministic tools or simple Shell/Python helpers for repeatable rule-based processing; feed structured summaries to AI and expand raw evidence only when needed |
| Automation lifetime | Promote helpers run-local → project → system only after reusable value is demonstrated |
| Model selection | Privacy-aware adaptive routing using minimum sufficient intelligence |
| Multi-agent model routing | Primary/subagents resolve models independently from business impact, complexity, risk and skill hints; use bounded context, escalation/de-escalation and minimum sufficient intelligence |
| Dynamic facts | Verify changing prices, versions and limits at runtime |
| Artifacts | Required outputs must be persisted in the project workspace |
| State | Workspace persistent state supports resume/handoff |
| Permissions | Least privilege and isolated change |
| Concurrency | Parallel read/review allowed; one writer per change boundary by default |
| Architecture | Clean Architecture principles where useful; DDD activated by domain complexity; avoid pattern-driven overengineering |
| Security assurance | Risk Profile → Product Baseline SAL + Change Security Impact → Effective SAL; critical dimensions impose hard floors |
| High-value business logic | Payments, refunds, stored value, balances, redeemable points/credits/vouchers/coupons and similar value flows are security boundaries |
| Security review scope | Review depth follows affected Change Boundary; high-risk product baseline alone does not force high-cost review for unrelated cosmetic changes |
| Security release gate | SAL 3–4 require applicable evidence; SAL 4 unresolved High/Critical findings block release |
| Assurance separation | Security Assurance, Reliability Impact and Model Tier remain distinct inputs |
| System maintenance | Every system change passes a Documentation Impact Gate; affected docs/flows/Mermaid diagrams/examples/scenarios/templates/version/changelog update together |
