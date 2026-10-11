# Skill Explorer｜技能圖鑑與使用範例

## Overview

AIPS Skill Explorer 是一頁式互動 Human Doc，列出最新 `skills/INDEX.yaml` 的所有可用 Skill。內容涵蓋繁體中文名稱、功能描述、Context Cost、觸發情境、Skill 原始路徑以及可複製的使用 Prompt。

<a href="./skill-explorer.html">開啟一頁式 Skill Explorer HTML</a>

目前整合基準：AIPS v0.82.0 main `123d0561`、Matt Pocock Skills `49dd158d`。本次整合採 Strategy B：全數盤點 38 個上游項目，重用既有能力，僅建立 5 個實質獨立的新 Skill，Writing 系列以明確要求才啟用，其他 Beta 不試驗。

## Usage

1. 開啟 HTML 圖鑑，在搜尋框輸入任務或 Skill 名稱。
2. 按領域（capability）和來源（AIPS 原有 / 本次整合）篩選。
3. 展開卡片查看適用觸發條件，複製繁體中文 Prompt，再依正常 AIPS 工作流程使用。
4. Human Docs 所列的「可用」僅表示 Registry 已有此 Skill；Runtime 是否能執行、操作是否需要授權，仍依 AIPS Harness、Project Mode、Human Authority 與當前工作環境決定。

## Source and Status

| 項目 | Canonical 來源 |
| --- | --- |
| Skill 功能、觸發、成本 | `skills/*/*/SKILL.md` frontmatter |
| 機器可讀 Registry | `skills/INDEX.yaml`，由 `scripts/skill_index.py` 產生 |
| 中文名稱與實務 Prompt | `docs/human/skill-examples.yaml` |
| 靜態一頁式 HTML | `docs/human/public/skill-explorer.html`，由 `scripts/skill_catalog.py` 產生 |
| Matt Pocock 38 項處置表 | `references/external-skills/mattpocock-2026-10-11.yaml` |

外部來源 [Matt Pocock Skills](https://github.com/mattpocock/skills) 採 MIT 授權；來源版本已固定，未自動下載或同步其 Beta / Misc內容。此整合不啟用新的 Git Publish 權限、部署或外部付費服務。
