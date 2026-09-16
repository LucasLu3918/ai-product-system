# AI Product System Bootloader

Do not load this entire repository.

1. Read `SYSTEM.md`.
2. Before any mutating implementation session, run the System Update Preflight: `aips preflight <project-path>`.
3. If the request changes this AI Product System, run System Self-Improvement Review and Constitution Impact Check before implementation.
4. For a large/core change, run the Core Change Approval Gate and wait for explicit approval.
5. Run task preflight before implementation.
6. Detect whether the task creates or materially revises the primary product/project plan.
7. For a primary planning task, resolve the persistence workspace first; if the user did not specify one, ask before creating the authoritative package.
8. Choose one primary work mode unless the request truly spans multiple modes.
9. Classify risk/security assurance when protected assets or reliability are relevant.
10. Resolve only the required roles and leaf skills.
11. For an existing project, discover applicable project instructions before generic knowledge.
12. Load only project context needed for the active task.
13. Never silently invent missing facts or force an unsuitable role to cover missing expertise.
14. Persist required outputs, execution state, and the exact system version/commit used in the project workspace.

Primary planning tasks follow `orchestration/PLANNING_PACKAGE.md`: persist the complete planning package, obtain Gate 1 approval, then present Initial Implementation Items + Recommended Implementation Flow and obtain Gate 2 approval before implementation.

If `aips` is not installed, follow `docs/INSTALLATION.md`. Do not bypass Update Preflight by performing an unsafe merge/rebase.

Human project decisions have the highest project authority, subject to external platform/tool restrictions and the protected safety boundary.

Risk-proportional security assurance follows `docs/SECURITY_ASSURANCE.md`. Do not skip required SAL 3–4 review, and do not over-apply SAL 4 review to unrelated cosmetic changes.


System self-improvement follows `orchestration/SYSTEM_SELF_IMPROVEMENT.md`. Constitution changes require a second explicit Constitutional Approval after risks are explained.

Before any remote Git publication, run the Git Publish Approval Gate: show changed files, change summary, validation evidence and atomic commit plan, then wait for explicit user approval.
