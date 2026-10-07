# Scenario 230: Compact Fixed System Context and Task Routes

## Given

- AIPS resolves a runtime-aware Turn Context for a project task.
- `SYSTEM_CORE.md` is the bounded fixed AIPS system policy alongside the existing bootstrap.
- Canonical protocols remain the authority for detailed task workflows.

## When

- The prompt asks for a publish, product-delivery, visual, security, testing, API/data, planning, documentation, general read, or general mutation task.
- A required core or route source is unavailable.

## Then

- The manifest and runtime hook expose the core path, selected route category, protocol IDs/paths, byte count, and resolution status without persisting the prompt.
- Unrelated protocol routes are not selected; unknown mutations conservatively select ORCHESTRATOR, CHANGE_IMPACT, and QUALITY_PLANNING.
- Missing required route sources are explicit and fail closed for mutation while preserving the universal core context.
- `SYSTEM.md` remains a compatible pointer to the core and canonical protocols.
- The core is at most 8192 bytes and the fixed AIPS context shrinks at least 60% against the pre-change system layer.
- Human Authority, instruction precedence, Change Impact, security, verification, and Git/release gates remain intact.

## Evidence

- `tests/evidence/intelligence_context_lifecycle.py`
- `tests/validation/static_contracts.py`
- `scripts/project_intelligence.py`
- `scripts/turn_context_hook.py`
