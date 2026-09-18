# 文件導覽

AIPS 將文件依主要讀者分流，避免 Human 說明與 Agent canonical contract 混在同一入口。

## Human-only 文件

永久 Human-only 文件統一放在 `docs/human/`。若某份獨立 Human report 因工具或產物需求必須持久放在其他位置，必須在 `config/documentation-audience.yaml` 明確登記，且檔名使用 `HUMAN_` prefix。

| 文件 | 用途 |
|---|---|
| `README.md` | Repository 第一入口、最短安裝/解除；屬 GitHub 慣例例外 |
| `docs/human/GETTING_STARTED.md` | 安裝一次後如何直接使用 Agent |
| `docs/human/INSTALLATION.md` | Install / Adapter / Cache / Attach / Uninstall |
| `docs/human/USER_GUIDE.md` | 完整工作方式 |
| `docs/human/HARNESS.md` | Turn-Aware Harness、Runtime Capability、Context Composition |
| `docs/human/PROJECT_INTELLIGENCE.md` | Existing Project 初始化、Review、Overrides、Freshness、Retrieval Intelligence / Quality Evaluation、Change Impact |
| `docs/human/CONFORMANCE.md` | Scenario Conformance、coverage 與 evidence |
| `docs/human/EVOLUTION_RADAR.md` | Weekly/Monthly research、Semantic Analysis、Human Decision、Controlled Trial |
| `docs/human/EVOLUTION_RADAR_OVERVIEW.html` | Evolution Radar 一頁完整圖解 |
| `docs/human/TECHNOLOGY_GUIDE.html` | AIPS 技術總覽、中英文專有名詞與可用情境 |
| `docs/human/DOCUMENTATION_SYNC.md` | Documentation Consistency + Audience Placement |
| `docs/human/SECURITY_ASSURANCE.md` | SAL、Secret/Credential Safety、Security Release evidence |
| `docs/human/ARCHITECTURE_OVERVIEW.md` | 人類架構總覽與圖示 |
| `docs/human/MAINTENANCE.md` | Maintainer 維護、Diagram Impact、Release 維護 |
| `docs/human/DOCUMENTATION_MAP.md` | 本文件 |

Human-only 圖示資產放在 `docs/human/assets/`。

## Agent / machine canonical 文件

| 位置 | 主要讀者 | 用途 |
|---|---|---|
| `AGENTS.md` | Agent | 最小 Bootloader |
| `SYSTEM.md` | Agent | System Router |
| `harness/HARNESS_PROTOCOL.md` | Agent / Maintainer | Global/Turn Harness contract |
| `harness/ADAPTER_CONTRACT.md` | Maintainer / Agent | Runtime capability / managed integration |
| `orchestration/*` | Agent / Maintainer | Execution contract、governance、routing、lifecycle |
| `roles/*` / `skills/*` | Agent | Responsibility / leaf expertise |
| `templates/*` | Agent / machine | Machine-validatable artifact contracts |
| `config/*` | Maintainer / machine | Deterministic policy/configuration |
| `references/*` | Agent / machine | Capability/reference registries |

## Shared canonical 文件

`docs/ARCHITECTURE.md` 同時供 Maintainer 與 Agent 使用，保存 detailed Mermaid architecture，因此保留在 `docs/` shared canonical root，不搬進 Human-only namespace。

Repository root 的 `README.md`、`CHANGELOG.md`、`SECURITY.md` 與 compatibility pointer `USER_GUIDE.md` 屬明確例外。

## 文件一致性

`config/documentation-sync.yaml` + `scripts/documentation_sync.py` 會將 behavior-bearing changed paths 映射到必須在同一 change review/update 的 Human / Agent docs。

`config/documentation-audience.yaml` + `scripts/documentation_audience.py` 另外確保：

- Human-only permanent docs 位於 `docs/human/`；
- `docs/` root 只保留 allowlisted shared canonical docs；
- active contracts 不再引用舊的 `docs/<human-file>` 路徑；
- standalone Human artifact 必須明確登記，並使用 `HUMAN_` prefix convention。

詳細說明見 [文件一致性契約](DOCUMENTATION_SYNC.md)。

Human Docs 使用繁體中文並在首次出現時保留重要英文術語；Agent Docs 以精簡英文為主。Large/Core Change 必須同時評估 Human Docs、Agent Docs 與 Architecture Diagram Impact。
