# Documentation Consistency Contract

Change Impact traversal 的使用與限制應在 Human Project Intelligence 指南、Technology Guide、架構概覽及本 orchestration 契約同步；Scenario 175 的 evidence 與 Conformance inventory 也必須保持一致。

OpenTelemetry export sources are mapped to the observability/run-state topics and Scenario 181. The projection stays derived and does not add a new authority surface.

## Purpose

Keep Human-facing and Agent-facing documentation synchronized with behavior-bearing AIPS changes.

Documentation completeness is part of implementation completeness. A change is not complete merely because code and tests pass while affected guidance, terminology or architecture descriptions remain stale.

## Authority

This contract does not create a new Human Approval Gate. It strengthens the existing Documentation Impact Gate with deterministic changed-path checks.

Canonical configuration: `config/documentation-sync.yaml`.
Validator: `scripts/documentation_sync.py`.
Human explanation: `docs/human/DOCUMENTATION_SYNC.md`.
Human technology inventory: `docs/human/TECHNOLOGY_GUIDE.md`.

## Audience synchronization

Portable Command Registry、CLI 與 MCP renderer 屬 Harness current behavior；同步 Human 文件時沿用既有 Harness、Architecture、Installation、Maintenance 與 Technology topic，不建立第二套文件樹。
When a configured behavior-bearing source path changes, the same change MUST update the mapped documentation surfaces:

- Human docs explain behavior, workflows, terminology and operational use in Traditional Chinese;
- Agent docs define concise execution contracts and authority boundaries in English;
- the Human Technology Guide is reviewed whenever configured technical implementation/contract surfaces change.

The mapping is explicit and deterministic. Do not guess from file names during validation.

Project Intelligence documentation mapping includes the stable intelligence implementation, rebuildable Retrieval Intelligence implementation, Retrieval Quality Evaluation harness, Structural Retrieval trial/adoption harness and provider-neutral local-first embedding Trial / optional remote operator-summary surfaces, including the dedicated semantic Trial dependency, so changes to indexing/ranking/context assembly/evaluation metrics, structural retrieval behavior or embedding Trial provider/privacy/operator-handoff contracts require the Human Project Intelligence guide, Agent protocol and Technology Guide to be reviewed together.

The same Project Intelligence mapping covers revision-aware Temporal Project Intelligence: changes to assertion validity intervals, supersession links, Git revision ancestry, current/as-of/between/why query semantics or provenance must synchronize the Human Project Intelligence guide, Technology Guide, Agent protocol and Conformance evidence. Unverifiable historical state remains UNKNOWN and is never promoted to a verified historical result.

## Technology Guide rule

新增 trajectory evaluator、trace template 或 Scenario evidence 時，必須同步更新 Trajectory Quality Gate protocol、Human Quality & Verification 說明，以及必要的 Scenario / Architecture Surface bindings。

`docs/human/TECHNOLOGY_GUIDE.md` is the maintained Human inventory of current AIPS techniques and terms. A configured technical change requires the guide to be updated in the same diff, and Documentation Placement additionally requires changed lines to land in the owning canonical topic instead of an append-only tail section.

Release history belongs in `CHANGELOG.md`; Scenario / verification history belongs in `docs/human/CONFORMANCE.md`. Legacy standalone HTML is compatibility-only.

## Validation behavior

Validation workflows keep generated Gate and Repository Health reports outside the checkout until the validation steps finish. Artifact upload preserves evidence without making generated files part of the documentation or revision binding.

`documentation_sync.py`:

1. validates `config/documentation-sync.yaml`;
2. receives changed files explicitly or resolves them from a Git comparison base;
3. matches changed behavior-bearing paths against configured rules;
4. requires every mapped Human and Agent document in the same change;
5. requires the Technology Guide when a configured technical path changed;
6. fails repository validation if a required documentation surface is missing from the diff.

Publication candidates run `scripts/repository_preflight.py` with an explicit base before the full lifecycle suite. `aips docs impact` computes the recursive sync and placement requirements up front. Git-ignored local metadata is excluded from audience-layout classification, while unignored unknown entries remain failures.

CI sets `AIPS_DOCS_DIFF_BASE` from the GitHub event base revision. Local validation without a known base still validates the contract/configuration, while focused checks may pass `--base-ref` or `--files` explicitly.

## Scope discipline

Structured Change Impact unknown dispositions extend the existing Change Impact contract. The validator, template, Human guidance and Scenario 179 evidence stay mapped to their canonical sections; a closed disposition never bypasses exact post-implementation diff reconciliation.

EARS requirement validator 測試契約屬於 Scenario Conformance trigger；功能實作、需求範本與 canonical planning 文件仍屬 Requirement Planning trigger，避免測試-only 修改擴張為無關文件改版。

Do not edit unrelated documentation merely to satisfy the validator. If a mapping becomes systematically noisy or inaccurate, change the mapping through normal AIPS maintenance review rather than bypassing the check.

The deterministic check proves that required documentation surfaces were reviewed in the same change. It cannot prove semantic correctness of prose. Semantic accuracy remains part of Author/Reviewer responsibility.

## Cross-document navigation

Human pages should link to relevant Human detail pages and, when useful for maintainers, canonical Agent protocols. Agent protocols may point to Human explanations but must keep canonical execution rules in Agent-facing protocol files rather than duplicating large Human guides.


## Human Documentation Namespace

Permanent Human-only documentation MUST live under `docs/human/`. The detailed audience policy is deterministic:

- config: `config/documentation-audience.yaml`;
- validator: `scripts/documentation_audience.py`;
- Human-only root: `docs/human/`;
- shared canonical docs under `docs/` require explicit allowlisting;
- standalone Human artifacts outside the Human root MUST be listed in `standalone_human_documents` and use the `HUMAN_` prefix.

Do not create a parallel `docs/agent/` tree. Existing `orchestration/`, `harness/`, Roles, Skills, templates and schemas remain canonical Agent/machine surfaces.


## Deterministic execution mapping

The Parallel Run Dashboard is registered as a read-only projection surface. Its implementation, checkpoint contract, orchestration protocol and Human guidance must remain synchronized without introducing a second state source or authority path.

The `deterministic-execution` rule binds Scheduler / Integration Gate implementation, Task Graph / Validation Profile contracts, validation dependencies and the GitHub validation workflow to their Human architecture/user guidance and Agent orchestration protocols.

The `requirement-planning` rule binds requirement clarification, Planning Package templates, the optional EARS requirements registry and its deterministic structure checker to User Guide / Technology Guide guidance, Scenario 174 evidence, and the canonical Agent protocols. The checker exposes JSON PASS/FAIL and zero/non-zero exit status for automation; these indicate structural validity only. Structure validation does not replace semantic review or test execution.

The publication-preflight mapping also covers candidate cleanliness, exact head/base binding, recursive documentation closure, Core Matrix changed-file hashes, browser smoke probes and the mandatory redacted secret scan over the exact final tree and complete candidate history. A system-browser launch crash is classified as an environment blocker and must not be reported as a product regression.

Independent review changes also synchronize the review task/context schemas, bounded packet and evidence contracts, Scheduler and Integration Gate behavior, scenario registry, Core Change Matrix, User Guide, Technology Guide, Security Assurance, Execution Isolation and requirement/planning protocols. Keep the attestation boundary explicit: structural validation cannot authenticate a reviewer; without a trusted runtime verifier, required review remains `UNVERIFIED` and blocks publication.

This keeps the runtime implementation, exact-candidate CI behavior and authority boundaries synchronized when future changes touch scheduling or Janitor behavior.

Installer and Harness runtime-path changes follow the same contract: update the mapped Human installation and integration guidance together with this Agent-facing synchronization record.


## Resource authorization mapping

The `resource-authorization` rule binds the deterministic evaluator, Resource Authorization Profile schema/template and Execution Profile reference to Human Architecture/User guidance plus Agent Execution Isolation/Orchestrator protocols. Any behavior change must keep default-DENY semantics, protected-authority boundaries and runtime-enforcement truth synchronized across those surfaces.

Execution Profile isolation fields now include optional minimum runtime class, provider verification state and data class. Changes must synchronize Execution Isolation, Orchestrator/Conformance guidance, User/Technology/Conformance docs and the sandbox provider registry. Source-transfer documentation must not imply authorization that is absent from the current policy.

Runtime Policy action schemas, deterministic decisions, hook capability claims and high-risk egress requirements are canonical in `orchestration/RUNTIME_POLICY_ENFORCEMENT.md`; synchronize them with Resource Authorization, Execution Isolation, Governance Audit, the adapter contract, Security Assurance, Harness and Scenario 177.


## Evolution Effectiveness mapping

The `evolution-radar` mapping includes the deterministic effectiveness script, policy config and monthly GitHub workflow. Changes to metric definitions, thresholds, source review flags, Issue publication behavior or authority fields must synchronize the canonical Evolution Radar / Execution Isolation Human and Agent docs plus the Technology Guide.


## Human documentation placement

The same canonical H2 placement contract applies to pre-commit working-tree preview and committed repository preflight. Preview includes tracked, staged, unstaged and untracked paths and identifies the allowed H2 for misplaced content.

Publication Preflight includes a working-tree preview and reports each closure path with its responsible placement or sync rule. This keeps the review actionable while both validators continue to enforce their existing contracts.

Runtime Content Safety Boundary 是跨 Security、Deterministic Execution 與 Publication 的正式 topic。其 behavior-bearing source 必須在 documentation placement registry 登錄，並由 Human docs、protocol 與 scenarios 保持一致。

External Eval / Red-Team Interoperability 的 Human placement 對應 Architecture Overview、Conformance、Security Assurance、User Guide、Technology Guide 與 Documentation Map。`orchestration/EVAL_INTEROPERABILITY.md` 是匯入格式、正規化 evidence fingerprint、外部 finding 人工確認與 AIPS Agent Eval promotion 的 canonical protocol；變更其 source、schemas、profile 或 lifecycle tests 時，應更新相應 Human topic 與 Scenario 180。

Current-behavior Human docs are topic-oriented, not release-note streams. `config/documentation-placement.yaml` maps behavior surfaces to allowed Human H2 sections. `scripts/documentation_placement.py` checks heading integrity and, when a diff base is available, verifies changed lines land inside allowed canonical sections.

Every behavior-bearing source that falls on the broad Technology Guide sync surface MUST also match a semantic placement rule. Unmapped new sources fail closed until maintainers assign the change to an existing canonical topic or deliberately add a new topic to the placement contract. This prevents future features from bypassing information architecture by merely appending prose at the end.

When a Scenario changes Runtime or MCP behavior, `orchestration/CONFORMANCE.md` is owned by the harness placement rule. A placement-contract update that assigns this ownership must synchronize the existing Runtime sections in Architecture Overview and Technology Guide plus the Human Documentation Sync and Map; it does not create a new product topic.

Temporal Project Intelligence evidence is recorded in the existing Project Intelligence / conformance surfaces, including Scenario 166 and its lifecycle evidence; it does not introduce a separate documentation namespace or approval path.

Do not satisfy documentation impact by appending a version/scenario note at the end of USER_GUIDE, ARCHITECTURE_OVERVIEW, HARNESS, INSTALLATION, TECHNOLOGY_GUIDE, or EVOLUTION_RADAR_OVERVIEW. Release history belongs in CHANGELOG; verification history belongs in CONFORMANCE.

`docs/human/` is also the VitePress source root. VitePress is a renderer only; it does not create a second canonical copy. PR/main can always validate the static build. GitHub Pages hosting is a separate repository setting: when not configured, deployment reports `SKIPPED_NOT_CONFIGURED` instead of misreporting a documentation build failure.
