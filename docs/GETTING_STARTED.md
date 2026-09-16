# 快速上手

這份文件給第一次使用 AI Product System 的人。

## 1. 安裝

完成 Git、Python 3 與 GitHub CLI（`gh`）設定後：

~~~bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
~~~

確認：

~~~bash
aips doctor
aips version
~~~

## 2. 初始化你的專案

~~~bash
aips init ~/Developer/projects/my-project
~~~

系統會建立專案狀態資料夾：

~~~text
.ai/
├── PROJECT.md
├── STATE.yaml
├── MANIFEST.yaml
└── SYSTEM.yaml
~~~

## 3. 每次實作前

執行系統更新預檢（System Update Preflight）：

~~~bash
aips preflight ~/Developer/projects/my-project
~~~

它只會安全更新 AI Product System，不會擅自 `git pull` 你的產品專案。

## 4. 開始交給 AI

範例：

~~~text
使用 ai-product-system 處理目前專案。

System:
~/Developer/ai-product-system

Target Project:
~/Developer/projects/my-project

先閱讀 AGENTS.md，再依 SYSTEM.md 路由。
如果有更適合的做法、重大風險或 Blocking Unknown，
請先提出建議，不要直接實作。
~~~

## 5. 常見使用方式

### 小型程式修改

直接說需求。系統會使用工程修改（Engineering Change）流程。

### 新產品

系統會先建立可重現規劃包（Reproducible Planning Package），先讓你審核規劃，再詢問是否進入實作。

### 視覺設計

你可以提供 Logo、商品照片、參考圖片、喜歡的網站、品牌規範或文字想法。系統會先做創意校準（Creative Calibration），再進入正式設計。

### 建立品牌

系統會從品牌目的、受眾、定位、價值、視覺與語調開始，不會只先做 Logo。完成後會保存成品牌系統（Brand System），未來其他作品可直接沿用。

### 大量固定資料處理

若只是固定規則的掃描、統計、轉換或驗證，系統會優先用 Shell 或簡單程式產生結構化結果，再由 AI 接續判斷，避免浪費 Token 解析原始資料。

## 6. 不知道怎麼描述也沒關係

你可以只說：

> 我想讓網站看起來比較高級、簡約，但現在 AI 做出來不像我想要的。

系統應先提供不同方向、參考與差異，引導你逐步校準，而不是要求你一次提供完整專業規格。

下一步：[完整使用指南](USER_GUIDE.md)
