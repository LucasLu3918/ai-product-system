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

若新 capability 沒有適合 section，應先設計新的 topic section並更新 placement config，而不是直接 append。

## Official Docs Site

docs/human/ 同時是 Official Docs Site 的 source；VitePress 只是 renderer。Website build output 不提交為 canonical content。

PR 會 build site；main 才具有 Pages deploy path。Workflow 會先讀取 repository Pages 狀態：已設定才 upload/deploy，未設定則明確記錄 `SKIPPED_NOT_CONFIGURED`。啟用 hosting 的一次性 repository 設定是 Settings → Pages → Build and deployment → Source = GitHub Actions。

Docs deployment 不取得 code merge、release 或 product production authority。

## Technology Guide

Canonical source 是 docs/human/TECHNOLOGY_GUIDE.md。舊 HTML 只保留 backward-compatible link stub。

## 文件互相導向

Getting Started / Installation / User Guide 以 task-oriented方式導覽；Architecture / Technology Guide 負責 explanation；Conformance 負責 reference/evidence history；Maintenance 文件給 maintainer。

## Deterministic protection

Documentation Sync 驗證「哪些文件必須一起改」；Documentation Placement 驗證「改動是否落到正確 topic section」。兩者都通過才代表文件同步完成。
