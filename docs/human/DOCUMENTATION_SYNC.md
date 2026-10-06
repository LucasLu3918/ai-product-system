# 文件一致性契約（Documentation Consistency Contract）

Runtime Context 的 Agent canonical 文件為 `orchestration/RUNTIME_CONTEXT.md`；Runtime Context、矩陣及 Scenario 198 改動時，需同步架構、Technology Guide、Conformance 與 Integration Gate 說明。

Human Docs 與 Agent canonical protocols 分工，但 behavior-bearing change 必須同步更新適用文件。

Retrieval relation extraction is an internal module behind the existing `retrieval_intelligence.py` facade. Changes preserve the public import and candidate evidence semantics, with the non-compiler-resolved boundary documented in Project Intelligence guidance.

Evolution deterministic pre-analysis follows the same facade rule: `evolution_analysis.py` remains the CLI/import entry point while `evolution_preanalysis.py` owns its implementation; behavior and authority documentation stay in the Evolution topics.

## 文件角色

~~~text
docs/human/*.md
→ Human current behavior / how-to / explanation

CHANGELOG.md
→ release history

docs/human/CONFORMANCE.md
→ verification / Scenario history

SYSTEM.md / orchestration / roles / skills
→ Agent canonical protocol
~~~

## Current-behavior placement contract

Release history keeps Unreleased, the latest five full releases and all stable version anchors in `CHANGELOG.md`; older full sections are manually archived without loss under `docs/history/changelog/`. The document-size audit remains report-only and never moves files.

共用快取解析器歸既有 publication-preflight 主題，套件安裝診斷器歸 installation 主題；修正與文件閉包一起驗證，不建立重複的治理或文件層。

Publication preflight changes synchronize the local Python/Node environment checks, GitHub workflow runtime pins, exact-candidate Gate instructions and Scenario 165. Local docs builds use Node 24+ and the installed VitePress bundle without package-manager or registry access.

OpenAPI contract tooling and its optional dependency file have an explicit placement rule: workflow commands belong in User Guide quality guidance, technical limits in the Technology Guide, and lifecycle claims in Scenario 194. Keep the Agent contract and Human descriptions synchronized when the validator or evidence schema changes.

Phase 3 Profile／Gate enforcement 另由 `implementation-enforcement` placement rule 綁定。新增 CLI、Profile 欄位、報告 schema 或 Scenario 195 行為時，同步檢查 User Guide、Architecture Overview、Technology Guide、Security Assurance 與 Conformance 的既有主題；維持「雜湊一致不等於 generator 已執行」與 Human authority 的界線。

Deterministic execution ownership 由 Scheduler、run state、projection 和 dashboard 共用同一個 canonical contract。更新 lease 或授權行為時，需同步更新 Human 操作／技術文件、run-state schema、Scenario 182 與 placement map。

Changes to turn intent, scoped instruction selection, event serialization, observed stage evidence, Agent Eval freshness and review attestation must update their canonical Human and orchestration sections together with `config/documentation-placement.yaml`.

Telemetry export sources map to the observability/run-state topics and Scenario 181; new source files must add a canonical placement rule before Human documentation is considered complete.

The `p17-required-files-parity-pilot` rule maps the versioned required-files mirror and its validator/lifecycle sources to Maintenance and Technology Guide. Changes to the placement registry itself also require updates to Architecture Overview, this contract, and Documentation Map.

`publication-transfer` placement rule 將新的 API transfer guard 與 lifecycle evidence 對應至 User Guide、Maintenance 和 Technology Guide 的現有章節；規則本身變更時仍需檢查 Architecture Overview、Documentation Map 及此文件的遞迴閉包。

提交前的 Publication Preview 會以工作樹為輸入檢查 H2 placement，包含已追蹤與未追蹤的新增內容；缺少 canonical H2 或內容落在不允許的段落時，診斷會列出允許的 H2。最終 Repository Preflight 仍驗證已提交的 diff。

`tests/validation/ears_requirement_contracts.py` 對應 Scenario Conformance；只有測試契約改動時更新 Conformance 與 Technology Guide，需求追蹤程式、規劃範本或 canonical requirement 文件仍觸發完整 Requirement Planning 閉包。

External Eval / Red-Team Interoperability 的來源由 `eval-interoperability` placement rule 綁定到 Architecture Overview、Conformance、Security Assurance、User Guide、Technology Guide 與 Documentation Map；`orchestration/EVAL_INTEROPERABILITY.md` 定義受限匯入、證據及人工確認流程，外部分數不直接成為 AIPS PASS/BLOCK。

Publication Preflight preview reports each required document with the sync or placement rule that introduced it, so maintainers can locate the exact source of recursive documentation requirements.

Keep the Node lockfile, npm CI installation and lockfile-triggered docs-site build aligned when changing documentation dependencies. GitHub merge-method reporting belongs to the existing publication-preflight guidance and does not change Human approval requirements.

Mandatory Candidate Secret Scanning extends the existing publication-preflight and security topics. The built-in scanner and policy must stay aligned across local preflight, Integration Gate and the early CI fail-fast step; all paths use the same exact candidate and redacted evidence contract.

Parallel Run Dashboard implementation and orchestration references use the registered dashboard placement contract, with operational behavior kept in the canonical run-state and execution sections.

Runtime Content Safety Boundary 的 behavior-bearing source 由 `config/documentation-placement.yaml` 的 `content-safety` rule 綁定到 Architecture Overview、Technology Guide、User Guide、Security Assurance、Maintenance 與 `orchestration/CONTENT_SAFETY_BOUNDARY.md`。新增 sink 或 detector 時，必須同步更新其 canonical placement 與 conformance scenario。

Independent review isolation is mapped by the `independent-review-isolation` rule to the task/context schemas, Scheduler, bounded review packet, Integration Gate evidence contract, scenario coverage and Human/Agent guidance. The mechanism is implemented but PR enforcement is disabled by default in the active matrix until trusted attestation is available. Keep exact candidate binding, read-only authority, context exclusions and verifier status consistent; structural evidence checks alone cannot mark a review verified.

Portable Command Registry、CLI lifecycle 與 MCP renderer 的 current behavior 由 Harness topic 說明；Host placement 未經官方能力驗證時，文件只能宣稱 AIPS-managed projection、MCP 或 generic fallback。

Requirement clarification 與 Planning Package 的變更由 requirement-planning placement rule 綁定至 User Guide 的需求釐清主題、Technology Guide 的 Product Delivery / Quality & Verification，以及對應的 Agent protocols。v2 Manifest、研究、domain 與 cross-artifact 範本由同一閉包維護，電商 domain pack 依索引觸發並按需載入。需求登錄檔和兩個檢查器只驗證結構及 ID 關聯；CLI 可輸出 JSON PASS/FAIL 並以零／非零退出碼表示結構檢查結果，語義審查與實際測試仍屬其他流程。

Implementation Resolution、Profile 範本、語言 Profile、結構驗證器與 Scenario 193 由同一 `requirement-planning` placement rule 綁定至 User Guide、Technology Guide、Architecture Overview、Conformance 和相關 Agent protocols。Profile validator 的 PASS 只表示結構符合，不代表語言、框架或架構建議經語義驗證。

Phase 4 generator adapter、報告 schema、Gate fixture 與 Scenario 196 沿用 `requirement-planning` placement closure；Human 文件同步標示本機 `--execute`、CI/Gate 不執行專案 generator、ownership/hash 保護與 subprocess 不具 OS sandbox 的限制。

Phase 5 的可選 Phase 4 report 核對及 Scenario 197 共用參考案例沿用同一 placement closure。User Guide 說明執行與多產品邊界；Technology Guide、Architecture Overview、Maintenance、Conformance 與 Documentation Map 同步記錄證據與適用限制。

Risk-adaptive Change Impact traversal 的操作流程與 READY 證據由 `orchestration/CHANGE_IMPACT.md` 定義；Human 使用方式落在 Project Intelligence 的 Change Impact topic，架構層次與限制同步到 Architecture Overview 和 Technology Guide。`tests/scenarios/175-risk-adaptive-bounded-impact.md` 綁定 lifecycle 與 contract evidence。

Structured Change Impact unknown dispositions remain in this same topic. Documentation Sync maps the validator, template and lifecycle evidence to the Project Intelligence, Change Impact and Conformance canonical sections; evidence requirements and legacy fail-closed behavior are not restated as a separate policy.
CI validation evidence is stored in the runner temporary directory until checks finish, then uploaded as artifacts. The report location does not become a repository documentation source or alter the exact revision being validated.

新功能不允許再使用「不知道放哪裡，所以在文件最後加一段 vX.Y 說明」的模式。

config/documentation-placement.yaml 定義 current-behavior 文件的 canonical H2 sections 與 subsystem → allowed placement mapping。scripts/documentation_placement.py 在 CI 檢查：

- current-behavior doc 必須只有一個 H1；
- 禁止以 vX.Y / Scenario N 當 current-behavior H2；
- 禁止 duplicate numeric H2；
- behavior-bearing source change 必須真的修改對應 Human doc；
- 所有會觸發 Technology Guide 的 behavior-bearing source 都必須命中一條 placement rule；沒有 mapping 就 fail closed；
- 每條 subsystem placement rule 也必須限制 Technology Guide 應更新的 canonical domain；
- changed lines 必須落在該 subsystem 的 allowed canonical section；
- legacy standalone HTML 不得再累加新 section。

Placement contract 本身新增 trigger 或 ownership 時，必須同步更新 Documentation Map、Architecture Overview、Technology Guide 與 Agent synchronization contract，讓新的 source → topic 關係可供讀者與 validator 查核。當 placement 調整是為既有 Runtime／MCP topic 補上 ownership，其新增說明仍留在既有 Runtime canonical section。

安裝、Harness 與 CI gate 的變更也必須在對應的 task-oriented Human 文件與 canonical 技術／架構區段留下可驗證說明。

Publication preflight 的 candidate resolver、browser runtime probe、clean checkout 與 Core Matrix hash binding 屬於既有 CI／Integration Gate topic；相關 source 變更必須同步 Human Map、Sync、Maintenance 與 Agent Gate protocol。

Temporal Project Intelligence 屬於 Project Intelligence 的既有 canonical topic：變更 temporal assertion schema、Git revision 查詢、validity/supersession 判定或 provenance 行為時，至少同步 Project Intelligence、Technology Guide、對應 Agent protocol 與 Conformance evidence；不得另建平行的時間軸文件。

Temporal 查詢的有效歷史以可驗證 Git revision 與 assertion provenance 為準；無法驗證的歷史只可呈現為 UNKNOWN，不得被 current/as-of/between/why 查詢當成已確認事實。

若新 capability 沒有適合 section，應先設計新的 topic section並更新 placement config，而不是直接 append。

Behavior-bearing source changes must first map every new source path in `config/documentation-placement.yaml` to its canonical Human topic and allowed H2 section. Update all required Human and Agent documents in the same change; diff-aware preflight checks both closure and changed-line placement.

## Official Docs Site

Pinned Actions updates require synchronized operational documentation. setup-node v7 executes with Node 24; upload-pages-artifact v5 uses upload-artifact v7. GitHub-hosted Ubuntu 24.04 supplies the runner; PR builds keep deployment skipped and main retains the configured Pages-state guard.

docs/human/ 同時是 Official Docs Site 的 source；VitePress 只是 renderer。Website build output 不提交為 canonical content。

PR 會 build site；main 才具有 Pages deploy path。Workflow 會先讀取 repository Pages 狀態：已設定才 upload/deploy，未設定則明確記錄 `SKIPPED_NOT_CONFIGURED`。啟用 hosting 的一次性 repository 設定是 Settings → Pages → Build and deployment → Source = GitHub Actions。

Docs deployment 不取得 code merge、release 或 product production authority。

## Technology Guide

Post-merge reconciliation is implemented in `scripts/publish_post_merge.py`; `scripts/publish_preflight.py` remains the compatible CLI facade. Keep both modules, lifecycle coverage and integration inventory synchronized when changing this boundary.

內部模組抽離若保留既有 CLI facade 與輸出，仍同步更新架構／文件觸發索引；操作說明只描述使用者可觀察的 current behavior。


Trajectory evaluator、trace template 或 Scenario evidence 的變更，必須同步更新 `docs/human/TECHNOLOGY_GUIDE.md` 的 Quality & Verification 說明與對應的 placement/Conformance bindings。

`config/system-facts.yaml` 保存 command、platform、runtime、optional dependency、validation 與 documentation bindings。執行 `python scripts/system_facts.py --write` 更新 `SYSTEM_REFERENCE.md` 的標記區塊；CI 以 `--check` 驗證來源與衍生表格一致。Generator 只產生表格，不改寫解釋性文字或 policy prose。

Canonical source 是 docs/human/TECHNOLOGY_GUIDE.md。舊 HTML 只保留 backward-compatible link stub。

## 文件互相導向

Getting Started / Installation / User Guide 以 task-oriented方式導覽；Architecture / Technology Guide 負責 explanation；Conformance 負責 reference/evidence history；Maintenance 文件給 maintainer。

## Deterministic protection

Document the shared Python bootstrap caller-declared import profile and dependency check alongside the canonical requirements and tested constraints.

The `tests/validate_repository.py` runner is part of the maintenance reliability closure: keep its exact-candidate optional-toolchain selection, OpenAPI evidence classification and subprocess environment isolation documented with the required repository aggregate boundary.

Evolution evaluation changes must synchronize the Human Radar guides, Scenario 218 and its Human/Agent conformance references with the `p16-evolution-human-evaluation` placement entry.

The runtime architecture inventory and System Reference are regenerated from canonical registries; CLI source modules are part of the runtime-context documentation trigger and must remain covered by the module-extraction lifecycle.

The pull-request advisory preflight is documented with the required full repository gate and its Scenario 220 contract; changes to either surface update the Human and Agent conformance records together.

Dependency update classification stays advisory and maps each package class to recommended evidence. Preserve unknown-package high-risk behavior, human decision authority, and the explicit prohibition on automatic merges and policy edits across the classifier, Scenario 221 and published guidance.

Document-size measurement remains informational: preserve the 50,000-byte threshold, non-blocking WARN behavior, and no-archive/no-move boundary across the audit, baseline and Scenario 222.

Changes to shared Python workflow bootstrap, timing bounds or concurrency policy update the affected Human maintenance/technology guidance, Scenario 207 evidence and Agent conformance crosswalk. Timeout rationale records sample count and observed range; concurrency serializes only identical-revision or same-cohort work and preserves distinct observation evidence. Evolution Effectiveness queues same-period Issue writes without cancelling any report.

New behavior-bearing scripts and workflows must receive an explicit source-to-topic placement before Human documentation changes. Validation and release additions also update their registered Scenario evidence and current conformance projection.

When maintenance validation behavior changes, keep scenario registration, full-run shadow safeguards, quality ratchets, and human-facing Gate descriptions synchronized. Reports may describe future selective behavior but cannot imply validators are skipped before a separate Human decision.

Python runtime floor、tested compatibility matrix 與排程 smoke workflow 共用 `system-facts` placement：事實由 `config/system-facts.yaml` 管理，System Reference 產生摘要，Installation 說明操作方式，Maintenance 說明驗證與修復，Technology Guide 記錄技術契約；相容性 workflow 的變更也必須更新這組文件。

Generated Conformance current and history views derive from the canonical registry and Human/Agent sources; regenerate both after scenario inventory or section changes. Historical anchors remain linked and are not silently removed.

Documentation Sync 驗證「哪些文件必須一起改」；Documentation Placement 驗證「改動是否落到正確 topic section」。兩者都通過才代表文件同步完成。

`aips docs impact --base <ref> --head <ref>` 會在發布前列出遞迴 sync requirement 與合法 placement section。Publication preflight 一律帶入明確 diff base；Git-ignored local metadata 不屬於 repository 文件候選。

Execution Isolation 的 provider registry、resolver、optional E2B smoke workflow、profile schema 與其 tests/scenarios 由 `execution-isolation` sync rule 綁定到 Architecture Overview、Security Assurance、Technology Guide、User Guide、Conformance 與 canonical Agent protocols。資料外送 adapter 未取得明確範圍前，文件與 workflow 維持 synthetic-only。

Runtime Policy Enforcement 的 action schema、deny-by-default evaluator、native hook decision 與高風險 sandbox 要求，沿用 Resource Authorization、Execution Isolation、Governance Audit 和 Security Assurance 文件閉包；Scenario 177 維護執行階段授權及限制的 evidence。

The `maintenance-reliability` mapping binds the bounded monthly collector, configuration, GitHub workflow, lifecycle and contract checks, Scenario 201, registry and evidence runner to the Human Maintenance / Conformance / Technology Guide / Documentation Map topics and the Agent Conformance protocol. Keep UNKNOWN handling, collection bounds, exact-SHA correlation and no-remediation authority aligned.

Exact-candidate browser toolchain selection is documented under the current-behavior placement contract: the central validator registry may skip browser-dependent render lifecycle checks only when a valid plan explicitly sets `needs_browser: false`; missing or invalid plans retain the full profile.

- Version-tag readiness changes also require the canonical release-readiness and Scenario 208 documentation placements; readiness remains separate from tag publication.

`scripts/retrieval_storage.py` shares the existing Project Intelligence placement and documentation-sync closure with `scripts/retrieval_intelligence.py`; new helper modules must be added to both canonical trigger lists before publication.
