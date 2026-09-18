# 文件一致性契約（Documentation Consistency Contract）

AIPS 將「程式、Agent contract、人類文件是否一起維持正確」視為完成條件的一部分，而不是發版前才人工補文件。

## 兩層 deterministic 保護

### 1. Documentation Sync

核心設定：[`config/documentation-sync.yaml`](../../config/documentation-sync.yaml)

檢查程式：[`scripts/documentation_sync.py`](../../scripts/documentation_sync.py)

Agent canonical protocol：[`orchestration/DOCUMENTATION_SYNC.md`](../../orchestration/DOCUMENTATION_SYNC.md)

當 behavior-bearing script / config / template / workflow / protocol 改變時，CI 依 changed-path mapping 要求相應 Human docs、Agent docs 與 Technology Guide 在同一 change 被 review / update。

Project Intelligence mapping 同時涵蓋 stable intelligence、`scripts/retrieval_intelligence.py` 與 `scripts/retrieval_evaluation.py`；未來 indexing、ranking、Git-history retrieval、token budgeting、context assembly 或 evaluation metrics 改變時，也必須同步 review Human / Agent Project Intelligence 文件。

### 2. Documentation Audience Placement

核心設定：[`config/documentation-audience.yaml`](../../config/documentation-audience.yaml)

檢查程式：[`scripts/documentation_audience.py`](../../scripts/documentation_audience.py)

永久 Human-only 文件統一放在：

```text
docs/human/
```

`docs/` root 只保留 allowlisted shared canonical documents，例如 `docs/ARCHITECTURE.md`。若單一 Human report 因 Artifact / export / workflow 限制必須持久存在其他位置，必須在 `config/documentation-audience.yaml` 的 `standalone_human_documents` 明確登記，並使用 `HUMAN_` prefix。

~~~text
Behavior-bearing technical change
        ↓
Documentation Sync mapping
        ↓
Human docs + Agent docs + Technology Guide
        ↓
Audience Placement validation
        ↓
Human-only docs in docs/human/
Shared canonical docs explicitly allowlisted
Legacy Human paths absent from active contracts
        ↓
Repository validation
~~~

## 文件角色

| 類型 | 主要位置 | 用途 |
|---|---|---|
| Human-only Docs | `docs/human/**` | 概念、操作、限制、案例、Human review |
| Agent canonical Docs | `orchestration/**`, `harness/**`, roles/skills | 執行契約、authority boundary、routing |
| Shared canonical Docs | explicit allowlist，例如 `docs/ARCHITECTURE.md` | Human / Agent 都會引用的 canonical technical source |
| Machine Contracts | `config/**`, `templates/**`, schemas | deterministic validation / generation |
| Standalone Human Reports | explicit registry + `HUMAN_*` | 不適合放入 Human namespace 的獨立持久輸出 |

## Technology Guide

[系統技術總覽](TECHNOLOGY_GUIDE.html) 受 Documentation Sync 管理。只要設定範圍內的技術實作、治理契約、workflow、重要 configuration 發生變更，本頁就必須在同一 change 被重新 review / update。

## 為什麼不建立 docs/agent？

AIPS 已經有 `orchestration/`、`harness/`、`roles/`、`skills/` 等 canonical Agent surfaces。再建立平行的 `docs/agent/` 會增加第二份 canonical source，因此不採用。

## 能保證什麼？

Deterministic validator 能保證：

- 設定範圍內的行為改變沒有完全漏掉文件；
- Human 與 Agent 文件一起進入 change；
- Human-only 文件位置明確；
- active contracts 不再使用已搬移的 legacy Human paths。

它不能單靠程式證明 prose 語意百分之百正確，因此 Author / Reviewer 仍需確認文件內容與實際行為一致。

## 文件互相導向

1. [文件導覽](DOCUMENTATION_MAP.md)
2. [系統技術總覽](TECHNOLOGY_GUIDE.html)
3. [架構總覽](ARCHITECTURE_OVERVIEW.md)
4. [Evolution Radar 完整圖解](EVOLUTION_RADAR_OVERVIEW.html)
5. [Evolution Radar 操作說明](EVOLUTION_RADAR.md)
