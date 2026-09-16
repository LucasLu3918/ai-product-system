# 文件導覽

AI Product System 將人類文件與 Agent 執行文件分開。

| 文件 | 主要讀者 | 用途 |
|---|---|---|
| `README.md` | Human | 第一入口 |
| `docs/GETTING_STARTED.md` | Human | 快速上手 |
| `docs/USER_GUIDE.md` | Human | 完整使用方式、Quality / Knowledge / Visual / Delivery |
| `docs/INSTALLATION.md` | Human | Install / Attach / Detach / Uninstall |
| `docs/ARCHITECTURE_OVERVIEW.md` | Human | 系統架構與產品生命週期 |
| `AGENTS.md` | Agent | 最小 Bootloader |
| `SYSTEM.md` | Agent | Routing |
| `orchestration/QUALITY_PLANNING.md` | Agent | Q1/Q2/Q3 與七大品質面向 |
| `orchestration/PROJECT_KNOWLEDGE.md` | Agent | 專案知識探索、Pointer、Staleness / Refresh |
| `orchestration/VISUAL_POLISH.md` | Agent | V1/V2 視覺一致性修復 |
| `orchestration/PRODUCT_DELIVERY.md` | Agent | LOCAL_COMPLETE / Production Enablement / PRODUCTION_VERIFIED |
| `roles/*` | Agent | Role 責任 |
| `skills/*` | Agent | Leaf Skill |
| `docs/ARCHITECTURE.md` | Maintainer / Agent | 詳細架構 |
| `docs/MAINTENANCE.md` | Maintainer / Agent | 系統維護與文件同步 |

Human Docs 使用繁體中文；專有名詞第一次出現附英文。Agent Docs 以精簡英文為主。

行為改變時，同時檢查 Human 與 Agent 文件是否需要更新。
