# Matt Pocock Skills — Strategy B integration review

Human intent (2026-10-11): incorporate all 38 upstream skills by documented disposition; merge overlapping capabilities, add only narrow reusable skills, include opt-in Writing methods, do not trial other Beta skills. Baseline AIPS main `123d0561ae32a18d96a2abd7e84991f7017911f8`, VERSION `0.82.0`; upstream `49dd158d1076134a641b33efb035946536778336` (MIT).

## Reuse-first admission

The inventory `references/external-skills/mattpocock-2026-10-11.yaml` records every source and its disposition. Existing owners remain canonical: code-review, tdd, systematic-debugging, domain-driven-design, clean-architecture, requirements-definition and delivery-planning. New skills have narrower responsibilities: `rapid-prototyping` (throwaway evidence, not production UI), `technical-research` (technical primary sources, not product market/visual research), `human-guided-wizard` (human-exclusive setup only), `technical-teaching` (learning/practice, not code delivery), and `creative-writing-workflow` (explicitly opt-in, three-phase writing; user-approved exception to general Beta exclusion).

Each new skill has exact input/output/trigger/non-trigger, model/context cost and no new authority. Upstream user-only vs automatic invocation differs by host; AIPS triggers for non-routine actions are explicit and never grant mutation rights. No new Role or Capability. Misc remains reference-only and Beta items other than Writing remain excluded from trial.

## Validation / authority

Canonical `SKILL.md` frontmatter feeds `skills/INDEX.yaml` using existing `scripts/skill_index.py`. Human Explorer must be generated from canonical registry and localized example metadata; no runtime capabilities are inferred from documentation. Include deterministic generation check and inventory coverage test. Verify affected existing scenarios 094, 225, runtime projections, document placement and relevant CI. No automatic deployment, release, merge or protected publication; use isolated review and required existing AIPS publication authority before protected actions. Human approval of strategy is not a claim of actual host tool-guard enforcement.

## Rollback

Revert the single isolated integration commit/PR without replacing preexisting Skill IDs or removing user-owned runtime skill files. Maintain upstream MIT attribution in intake records and derivative documentation.
