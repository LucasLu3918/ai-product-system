# 文件導覽

AI Product System 將人類使用文件與 Agent 執行文件分開，避免單一文件同時服務兩種讀者而變得冗長。

| 文件 | 主要讀者 | 用途 |
|---|---|---|
| `README.md` | Human | 第一入口 |
| `docs/GETTING_STARTED.md` | Human | 5 分鐘快速上手 |
| `docs/USER_GUIDE.md` | Human | 完整使用方式 |
| `docs/INSTALLATION.md` | Human | 安裝、更新、解除安裝 |
| `docs/ARCHITECTURE_OVERVIEW.md` | Human | 系統架構圖、完整產品交付流程與簡介 |
| `AGENTS.md` | Agent | 最小 Bootloader |
| `SYSTEM.md` | Agent | Routing |
| `orchestration/*` | Agent | 需要時載入的 Protocol |
| `roles/*` | Agent | Role 責任 |
| `skills/*` | Agent | Leaf Skill |
| `docs/ARCHITECTURE.md` | Maintainer / Agent | 詳細架構 |
| `docs/MAINTENANCE.md` | Maintainer / Agent | 系統維護與文件同步 |

## 語言規則

Human Docs：繁體中文；專有名詞第一次出現標註英文。

Agent Docs：以精簡英文為主，避免同一規則維護雙語版本。

## 同步規則

如果 Agent 行為改變，檢查 Agent Docs。

如果使用方式改變，檢查 Human Docs。

如果兩者都受影響，兩邊都必須同步更新。
