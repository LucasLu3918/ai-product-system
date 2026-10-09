# Plan25 Phase 3 CI and Quality Evidence

Date: 2026-10-09
Base: Phase 2 candidate `a2315d96e4e4c20d73300ada351647448eda5dbb`
Scope: full-run shadow validation, graduation evidence, quality ratchets and measured module work.

## Selective validation

- `config/validation-graduation.yaml` keeps `mode: full_run_shadow`, `selective_execution_enabled: false`, `human_decision_required: true`, and automatic activation disabled.
- Core, Large, release, unknown and governance/validator paths retain full validation.
- The graduation evaluator requires complete artifact history, at least 30 observation days, 30 unique PRs, zero false negatives and a Human decision.
- A Core shadow plan for the current baseline selected all 61 validation modules for actual runs, had `full_validation_fallback: true`, `would_skip: []`, `unknown_paths: []`, and `replay_status: NOT_RUN`. The plan is advisory and did not skip any execution.
- `validation_shadow_plan_lifecycle.py` and `validation_graduation_lifecycle.py` passed their synthetic contract cases. They are not a measured PR cohort. This task did not collect real cohort/replay history, so graduation is not established.

## Quality and modules

- The latest exact-candidate Core Gate reported 689 Ruff findings against the repository baseline of 758, with no new findings in changed code; the candidates changed no Python files.
- Selected Mypy findings: 0 against a zero-finding budget.
- `quality_ratchet_lifecycle.py` passed.
- Coverage remains branch-measured and report-only, with no repository-wide minimum. The bounded storage baseline is not representative evidence for a global threshold.
- Existing module budgets identify next targets in `project_intelligence.py` and `retrieval_intelligence.py`; these evidence-only candidates contain no module changes and establish no measured hot spot that would justify a refactor.

## Decision

The current policies and contracts are already conservative and internally consistent. Keep selective execution disabled until the real cohort meets every graduation requirement. Keep the existing touched-code ratchet, selected Mypy policy, module budgets and report-only coverage policy; do not introduce a broad coverage target or refactor without measured evidence.
