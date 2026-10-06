# Scenario 207: Shared Python bootstrap action

Given a pilot workflow that declares its Python version and dependency files, when the local composite action runs, then it uses the pinned setup action, installs all declared requirements and optional constraints, and preserves caller permissions and pull request triggers. Scheduled and manual Evolution Effectiveness runs that reconcile the same monthly Issue also share a repository-scoped, non-cancelling queue; custom periods remain separate and every queued report is preserved.

Evidence: `tests/evidence/python_bootstrap_action_lifecycle.py`.
