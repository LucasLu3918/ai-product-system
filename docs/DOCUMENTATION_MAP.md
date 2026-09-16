# 文件導覽

| 文件 | 主要讀者 | 用途 |
|---|---|---|
| `README.md` | Human | 第一入口、最短安裝/解除 |
| `docs/GETTING_STARTED.md` | Human | 安裝一次後如何直接使用 Agent |
| `docs/INSTALLATION.md` | Human | Install / Adapter / Cache / Attach / Uninstall |
| `docs/HARNESS.md` | Human | Turn-Aware Harness、Runtime Capability、Context Composition |
| `docs/PROJECT_INTELLIGENCE.md` | Human | Existing Project 初始化、HTML Review、Overrides、Freshness、Change Impact |
| `docs/SECURITY_ASSURANCE.md` | Human / Reviewer | SAL、Secret/Credential Safety、Security Release evidence |
| `docs/USER_GUIDE.md` | Human | 完整工作方式 |
| `docs/ARCHITECTURE_OVERVIEW.md` | Human | 系統架構總覽 |
| `AGENTS.md` | Agent | 最小 Bootloader |
| `SYSTEM.md` | Agent | System Router |
| `harness/HARNESS_PROTOCOL.md` | Agent / Maintainer | Global/Turn Harness contract |
| `harness/ADAPTER_CONTRACT.md` | Maintainer | Runtime capability / managed integration |
| `orchestration/TURN_HARNESS.md` | Agent | 每 Turn context contract |
| `orchestration/PROJECT_INTELLIGENCE.md` | Agent | Project Intelligence canonical protocol |
| `orchestration/CHANGE_IMPACT.md` | Agent | Existing-project mutation impact guard |
| `orchestration/SECRET_HANDLING.md` | Agent / Reviewer | Key/Token/Password secure acquisition、redaction、exposure response |
| `orchestration/CORE_CHANGE_TESTING.md` | Agent / Reviewer | Large/Core Change 的 affected-boundary Test Matrix |
| `orchestration/PROJECT_KNOWLEDGE.md` | Agent | v0.8 compatibility/migration only |
| `orchestration/QUALITY_PLANNING.md` | Agent | Q1/Q2/Q3 Quality Planning |
| `orchestration/VISUAL_POLISH.md` | Agent | V1/V2 Visual Consistency |
| `orchestration/PRODUCT_DELIVERY.md` | Agent | LOCAL_COMPLETE / Production |
| `roles/*` / `skills/*` | Agent | 責任與 Leaf expertise |
| `docs/ARCHITECTURE.md` | Maintainer / Agent | 詳細 Architecture / Mermaid |
| `docs/MAINTENANCE.md` | Maintainer | System maintenance / Diagram Impact |

Human Docs 使用繁體中文；Agent Docs 以精簡英文為主。Large/Core Change 必須檢查 Human Docs、Agent Docs 與受影響 Architecture Diagrams。
