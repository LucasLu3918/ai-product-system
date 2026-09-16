# Scenario Conformance

AIPS v0.13 開始把「Acceptance Scenario 有幾份」與「有多少真的有可追溯測試證據」分開。

## Coverage 類型

- `deterministic`：可由 deterministic helper / schema / rule test 驗證。
- `lifecycle`：需要多步驟執行流程的 executable test。
- `agent_eval`：需要 Agent / Model 行為評估。
- `manual`：規格存在且可人工檢查，但目前不宣稱 automated evidence。
- `uncovered`：尚無可接受 evidence；目前 release policy 不允許 uncovered。

## 指令

~~~bash
aips conformance check
aips conformance report
~~~

Registry 位於 `tests/scenario_coverage.yaml`。

## v0.13 Baseline

v0.13 發布時採保守分類：既有 001–095 若沒有明確的一對一 executable evidence，就維持 `manual`。這不是表示它們沒有任何 validator 關聯，而是 AIPS 不把間接相關檢查誇大成 Scenario-level automation。

Coverage percentage 是工程 evidence 指標，不是系統品質分數，也不能取代 risk-based testing。

## v0.14 Baseline

v0.14 新增 Scenario 111–115，全部都有直接 executable evidence：2 個 deterministic、3 個 lifecycle。若既有 001–095 不重新分類，release baseline 為 115 個 Scenario、95 manual、20 automated、0 uncovered。

## v0.14.1 Legacy Scenario Reconciliation

v0.14.1 重新核對 Scenario 001–095 與目前 canonical contracts，先修正規格漂移，再提升 automation evidence，避免把過時行為固定成自動化測試。

已修正的主要 drift 包含：

- Update Preflight：沒有 `.ai/` 的 Project 保持 EPHEMERAL，不再自動 Attach。
- Project Knowledge：新 reusable understanding 以 Project Intelligence + SOURCE_REGISTRY 為 canonical；`.ai/knowledge/` 僅保留 migration compatibility。
- Runtime instruction integration：Codex / Claude 使用 managed composition 保存既有使用者內容，不再因為檔案已存在就一律降為 MANUAL。
- Harness lifecycle：ownership 以 managed block / namespaced hook 為單位安全移除；使用者內容與 unrelated settings 必須保留。
- Runtime capability：Context Capability 與 Governance Enforcement 維持兩個獨立 truth axes。

新增 direct evidence：

- `tests/evidence/adapter_composition.py`
- `tests/evidence/project_intelligence_lifecycle.py`
- `tests/evidence/secret_safety.py`

只有這些 evidence 實際覆蓋的 legacy Scenario 才從 `manual` 提升為 `deterministic` / `lifecycle`。

v0.14.1 baseline：

~~~text
Total       115
Manual       77
Automated    38
Uncovered     0
Automated   33.0%
~~~

仍為 manual 的 Scenario 不代表失敗；它們通常包含需要 Agent judgment、Human decision、外部環境或跨文件語意評估的行為，目前不會為提高百分比而虛假標記為 automated。

## v0.15 Baseline

Canonical Project Identity / Resume Integrity 新增 Scenario 116–120，全部具 executable evidence：

~~~text
Total       120
Manual       77
Deterministic 15
Lifecycle    28
Agent Eval    0
Automated    43
Uncovered     0
Automated   35.8%
~~~

Identity/Resume evidence 同時驗證跨 worktree repository identity、dirty workspace STALE、legacy run migration、repository-wide Single Writer 與 Project Intelligence canonical namespace。

## v0.16 Agent Eval Conformance

需要 Agent 語意判斷的 Scenario 不再只能停留在 manual，也不會被硬改成 deterministic test。

流程：

~~~text
Eval Case
→ 任一 Provider / Runtime 的實際 Agent 執行
→ Observable structured response
→ Recorded Result
→ Case SHA-256 fingerprint binding
→ Deterministic rubric scoring
→ PASS / FAIL
~~~

AIPS Core 不在 CI 裡呼叫特定模型 API。CI 驗證的是已記錄的 observable Result 是否仍綁定目前 Case，以及 rubric 是否通過。

第一批 Agent Eval：

~~~text
017 Core Change Approval
019 System Self-Improvement
020 Constitutional Change
025 Avoid Duplicate Role
035 Requirement Clarification
041 Multi-Perspective Review
042 Author Fix / Targeted Re-review
094 New Skill Admission
~~~

另外新增 Scenario 121–125 驗證 Agent Eval framework 自身的 fingerprint、result binding、rubric、privacy/provider-neutral 與 lifecycle。

v0.16 baseline：

~~~text
Total         125
Manual         69
Deterministic  19
Lifecycle      29
Agent Eval      8
Automated      56
Uncovered       0
Automated     44.8%
~~~

Agent Eval Result 禁止保存 Chain-of-Thought、private reasoning、scratchpad 與 Secret-like value。Case 修改後舊 Result fingerprint 失效，必須重新執行 Agent，不可只改 fingerprint。

## v0.16.1 Focused Harness Evidence Maturity

不改 Harness 行為，只把已能以隔離 runtime fixture 真正重現的 legacy manual Scenario 升級為 lifecycle evidence：

~~~text
057 Global Harness Automatic Bootstrap
061 EPHEMERAL Project Does Not Auto-Attach
066 Gemini Namespaced Extension
067 Failed Adapter Uninstall Preserves Ownership
072 Gemini BeforeAgent Turn Context
073 Runtime Capability Truth
~~~

直接 evidence：`tests/evidence/harness_runtime_lifecycle.py`。

它驗證 managed composition、Gemini official extension link/uninstall、BeforeAgent、user GEMINI/settings preservation、EPHEMERAL resolve、Context Capability / Governance Enforcement truth，以及 uninstall failure → ownership preserved → safe retry。

v0.16.1 baseline：

~~~text
Total         125
Manual         63
Deterministic  19
Lifecycle      35
Agent Eval      8
Automated      62
Uncovered       0
Automated     49.6%
~~~

011 / 044 / 069 等仍維持 manual，直到有足夠隔離、完整的一對一 install/preflight evidence；不因鄰近 validator 而直接升級。
