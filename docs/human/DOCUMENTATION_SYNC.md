# 文件一致性契約（Documentation Consistency Contract）

Human Docs 與 Agent canonical protocols 分工，但 behavior-bearing change 必須同步更新適用文件。

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

OpenAPI contract tooling and its optional dependency file have an explicit placement rule: workflow commands belong in User Guide quality guidance, technical limits in the Technology Guide, and lifecycle claims in Scenario 194. Keep the Agent contract and Human descriptions synchronized when the validator or evidence schema changes.

Phase 3 Profile／Gate enforcement 另由 `implementation-enforcement` placement rule 綁定。新增 CLI、Profile 欄位、報告 schema 或 Scenario 195 行為時，同步檢查 User Guide、Architecture Overview、Technology Guide、Security Assurance 與 Conformance 的既有主題；維持「雜湊一致不等於 generator 已執行」與 Human authority 的界線。

Deterministic execution ownership 由 Scheduler、run state、projection 和 dashboard 共用同一個 canonical contract。更新 lease 或授權行為時，需同步更新 Human 操作／技術文件、run-state schema、Scenario 182 與 placement map。

Changes to turn intent, scoped instruction selection, event serialization, observed stage evidence, Agent Eval freshness and review attestation must update their canonical Human and orchestration sections together with `config/documentation-placement.yaml`.

Telemetry export sources map to the observability/run-state topics and Scenario 181; new source files must add a canonical placement rule before Human documentation is considered complete.

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

## Official Docs Site

docs/human/ 同時是 Official Docs Site 的 source；VitePress 只是 renderer。Website build output 不提交為 canonical content。

PR 會 build site；main 才具有 Pages deploy path。Workflow 會先讀取 repository Pages 狀態：已設定才 upload/deploy，未設定則明確記錄 `SKIPPED_NOT_CONFIGURED`。啟用 hosting 的一次性 repository 設定是 Settings → Pages → Build and deployment → Source = GitHub Actions。

Docs deployment 不取得 code merge、release 或 product production authority。

## Technology Guide

Trajectory evaluator、trace template 或 Scenario evidence 的變更，必須同步更新 `docs/human/TECHNOLOGY_GUIDE.md` 的 Quality & Verification 說明與對應的 placement/Conformance bindings。

Canonical source 是 docs/human/TECHNOLOGY_GUIDE.md。舊 HTML 只保留 backward-compatible link stub。

## 文件互相導向

Getting Started / Installation / User Guide 以 task-oriented方式導覽；Architecture / Technology Guide 負責 explanation；Conformance 負責 reference/evidence history；Maintenance 文件給 maintainer。

## Deterministic protection

Documentation Sync 驗證「哪些文件必須一起改」；Documentation Placement 驗證「改動是否落到正確 topic section」。兩者都通過才代表文件同步完成。

`aips docs impact --base <ref> --head <ref>` 會在發布前列出遞迴 sync requirement 與合法 placement section。Publication preflight 一律帶入明確 diff base；Git-ignored local metadata 不屬於 repository 文件候選。

Execution Isolation 的 provider registry、resolver、optional E2B smoke workflow、profile schema 與其 tests/scenarios 由 `execution-isolation` sync rule 綁定到 Architecture Overview、Security Assurance、Technology Guide、User Guide、Conformance 與 canonical Agent protocols。資料外送 adapter 未取得明確範圍前，文件與 workflow 維持 synthetic-only。

Runtime Policy Enforcement 的 action schema、deny-by-default evaluator、native hook decision 與高風險 sandbox 要求，沿用 Resource Authorization、Execution Isolation、Governance Audit 和 Security Assurance 文件閉包；Scenario 177 維護執行階段授權及限制的 evidence。
