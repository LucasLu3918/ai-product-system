# 文件導覽

AI Product System 將人類文件與 Agent 執行文件分開。

| 文件 | 主要讀者 | 用途 |
|---|---|---|
| README.md | Human | 第一入口、最短安裝/解除 |
| docs/GETTING_STARTED.md | Human | 第一次安裝、Harness 驗證、開始使用 |
| docs/INSTALLATION.md | Human | 完整 Install / Adapter / Ephemeral / Attach / Uninstall / Reinstall |
| docs/HARNESS.md | Human | Global Harness、Runtime Coverage、Ownership、Instruction Composition |
| docs/USER_GUIDE.md | Human | 完整使用方式、Quality / Knowledge / Visual / Delivery |
| docs/ARCHITECTURE_OVERVIEW.md | Human | 系統與 Harness 架構總覽 |
| AGENTS.md | Agent | 最小 Bootloader |
| SYSTEM.md | Agent | Routing |
| harness/BOOTSTRAP.md | Agent Runtime | 自動接入時的 Minimal Bootstrap |
| harness/HARNESS_PROTOCOL.md | Agent / Maintainer | Global Harness 行為與 ownership |
| harness/ADAPTER_CONTRACT.md | Maintainer | Runtime Adapter contract |
| orchestration/HARNESS_RESOLUTION.md | Agent | Runtime/Project/Ephemeral/Attached resolution |
| orchestration/QUALITY_PLANNING.md | Agent | Q1/Q2/Q3 與七大品質面向 |
| orchestration/PROJECT_KNOWLEDGE.md | Agent | 專案知識探索、Pointer、Staleness / Refresh |
| orchestration/VISUAL_POLISH.md | Agent | V1/V2 視覺一致性修復 |
| orchestration/PRODUCT_DELIVERY.md | Agent | LOCAL_COMPLETE / Production Enablement / PRODUCTION_VERIFIED |
| roles/* | Agent | Role 責任 |
| skills/* | Agent | Leaf Skill |
| docs/ARCHITECTURE.md | Maintainer / Agent | 詳細架構與 Mermaid |
| docs/MAINTENANCE.md | Maintainer / Agent | 系統維護、文件/架構圖同步 |

Human Docs 使用繁體中文；專有名詞第一次出現附英文。Agent Docs 以精簡英文為主。

大型/Core Change 必須檢查 Human Docs、Agent Docs 與 Architecture Diagrams 是否同步。
