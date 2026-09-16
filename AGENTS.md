# AI Product System Bootloader

Do not load this entire repository.

1. Read `SYSTEM.md`.
2. Before any mutating implementation session, run the System Update Preflight: `aips preflight <project-path>`.
3. Run task preflight before implementation.
4. Detect whether the task creates or materially revises the primary product/project plan.
5. For a primary planning task, resolve the persistence workspace first; if the user did not specify one, ask before creating the authoritative package.
6. Choose one primary work mode unless the request truly spans multiple modes.
7. Resolve only the required roles and leaf skills.
8. For an existing project, discover applicable project instructions before generic knowledge.
9. Load only project context needed for the active task.
10. Never silently invent missing facts or force an unsuitable role to cover missing expertise.
11. Persist required outputs, execution state, and the exact system version/commit used in the project workspace.

Primary planning tasks follow `orchestration/PLANNING_PACKAGE.md`: persist the complete planning package, obtain Gate 1 approval, then present Initial Implementation Items + Recommended Implementation Flow and obtain Gate 2 approval before implementation.

If `aips` is not installed, follow `docs/INSTALLATION.md`. Do not bypass Update Preflight by performing an unsafe merge/rebase.

Human project decisions have the highest project authority, subject to external platform/tool restrictions and the protected safety boundary.
