# 快速上手

## 1. 安裝一次

~~~bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
~~~

確認：

~~~bash
aips version
aips harness status
aips harness doctor
~~~

## 2. 平常直接使用 Agent

安裝完成後，直接開 Codex CLI、Claude Code 或 Gemini CLI 對談，不需要每次先輸入 AIPS 指令。工程任務會組合 AIPS Rules、Runtime/User Instructions、Project Instructions/Docs、Project Intelligence 與 Current Prompt。

## 3. Runtime Capability

- TURN_NATIVE：原生 per-prompt Hook，在 planning 前加入 Context。
- CONTEXT_ALWAYS：持久 instruction 要求每個工程 Turn Resolve AIPS Context。
- MANUAL：需要人工接入。
- UNSUPPORTED：沒有安全支援方式。

實際結果以 `aips harness status` / `aips harness doctor` 為準。

## 4. 第一次修改既有專案

~~~text
Existing Project
→ Read-only Intelligence Bootstrap
→ Existing Instructions / Docs
→ Repository Topology
→ Architecture / Data Flow / Modules
→ API / DB / Events / Consumers
→ Conventions / Testing / Security / Operations
→ Semantic Enrichment
→ READY
→ Change Impact
→ Implementation
~~~

使用者不需要先手動初始化；Agent 依 Turn Context 自動完成必要步驟。

## 5. EPHEMERAL 也能重用

沒有 `.ai/` 時，Project Intelligence 可存在：

~~~text
~/.config/aips/projects/<project-id>/intelligence/
~~~

要改為 Project-local persistence 才執行 `aips attach /path/to/project`。Attach/Detach 會安全搬移或同步 Intelligence。

## 6. Human Review HTML

第一次 Intelligence 完成或有重大更新時會產生 `PROJECT_INTELLIGENCE_REVIEW.html`。使用者的補充、例外與排除條件由 Agent 保存到 `PROJECT_OVERRIDES.yaml`；HTML 本身不是 Source of Truth。

## 7. Change Impact

Existing Project Mutation 前會檢查 Input、Output、DB/Cache、Events、Consumers、Security、Business Invariants、Compatibility、Tests、Observability 與 Contracts，再依有效的 Project-native Style 實作。

## 8. 解除

`aips uninstall` 預設保留 User instructions、Skills、Project source、`.ai/` 與 External Project Intelligence。只有 `aips uninstall --remove-cache` 才移除 External Cache。
