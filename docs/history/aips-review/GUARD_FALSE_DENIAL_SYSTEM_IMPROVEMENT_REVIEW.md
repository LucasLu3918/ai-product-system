# System Improvement Review：發布守衛誤擋與診斷碼不一致

- 狀態：APPROVED（2026-10-19，使用者確認方向與範圍，不含 LATER 項目）；實作差異記錄於 `GUARD_FALSE_DENIAL_CORE_CHANGE_PROPOSAL.md`
- 日期：2026-10-19
- 對應分析項目：第 2、3、4、5 項

## Appropriateness

適當。四個問題都已在本機用實際 hook 輸入重現；它們都是「與發布無關、或可安全檢查的指令被拒絕」，以及一個診斷對照缺漏的 bug。受保護發布操作（push、PR create、merge、tag、release）的授權語意不變。

## User problem

Agent 的日常唯讀指令與標準 commit 寫法被 `governance_guard.py` 拒絕，迫使 agent 改寫指令、多花工具呼叫，且拒絕訊息的診斷碼與原因不一致，難以排除。

## Proposed solution

1. 第 2 項：放寬唯讀指令的誤擋（動態執行檔路徑、動態 `-C/--repo`、`gh api` GET、Git alias 與 `git lfs`）。
2. 第 3 項：支援 Claude Code 標準 commit 形式（引號 heredoc 訊息、`git add … && git commit`、`-a`、`--amend`），並把 commit 階段的 `REVIEW` 改為警告。
3. 第 4 項：未追蹤檔案不再擋 push / PR。
4. 第 5 項：修正命令分類錯誤碼落入 `INTERNAL_DIAGNOSTIC_GAP` 的問題。

## 本次審查對原提案的修正（重要）

- **撤回「commit 階段 REVIEW 改為警告」**。先前說「push/PR 階段才擋」不正確：push 階段的 `scan_candidate`（`check_secret_leakage.py`）只掃密鑰，不做 injection 分類。若 commit 階段放行 `REVIEW`，injection 訊號在本機就完全不會被擋，這是安全邊界的實質削弱。建議改列 LATER，需搭配 push 階段補上 injection 掃描後再做。
- 第 3 項的 `git add … && git commit` 不能只放寬語法：hook 執行時 `git add` 尚未發生，現有流程只掃暫存區，會漏掃即將加入的檔案。實作必須額外掃描「即將被加入的工作樹版本」，這是範圍中最大的一塊。

## Existing coverage

- `scripts/publication_commands.py`：bashlex AST 解析、heredoc 遮罩、巢狀替換。
- `scripts/governance_guard.py`：`operations_for`、`_direct_operations`、`commit_safety`、`deny_hook_input`。
- `scripts/publication_authority.py`：`PublicationError.diagnostic()`、`PUBLICATION_DIAGNOSTICS(_ZH)`、`worktree_dirty_details`、`action()`。
- `scripts/publication_planning.py`：post-merge reconciliation 的乾淨檢查。
- 測試：`tests/test_publication_authority.py`（`ShellTest`、hook 測試、`commit_safety` 測試）、`tests/test_publication_planning.py`、Scenario 099 / 169 / 261。
- 先例：`.aips/review/CLAUDE_SHELL_EXPANSION_SYSTEM_IMPROVEMENT_REVIEW.md` 已用同一方式擴充解析器。

## Reuse / extension candidates

只擴充上列既有模組與測試，不新增 Role、Skill、Capability、Gate 或設定檔。

## Lower-layer alternative

| 項目 | 不改程式的替代做法 | 為何不足 |
|---|---|---|
| 未追蹤檔擋 push | 把檔案加進 `.git/info/exclude` | 每個暫存草稿都要手動排除，摩擦持續存在 |
| 動態 `-C` / 執行檔 | 改寫成字面路徑 | agent 每次被擋後才改寫，浪費一輪 |
| commit heredoc | 先寫入訊息檔再 `git commit -F file` | 可行但與 Claude Code 內建慣例衝突，agent 預設一定會先被擋 |
| 診斷碼 | 無 | 屬程式 bug |

## 具體行為變更

| 指令 | 現在 | 變更後 |
|---|---|---|
| `git -C $PWD status`、`gh --repo "$(…)" pr view` | 拒絕 `DYNAMIC_CLI_OPTION` | 放行（動態值只在動詞為發布動作時拒絕） |
| `git -C $X push …`、`git -c "$X" status` | 拒絕 | 維持拒絕（`-c`、`--config-env`、`--exec-path` 動態值一律拒絕） |
| `$G/.venv/bin/python x.py` | 拒絕 `DYNAMIC_EXECUTABLE` | 放行（目錄動態、檔名為字面且非 git/gh/shell/包裝器時，依檔名分類） |
| `$X push`、`"$x" push`、`git${E} push`、`$D/git push` | 拒絕 | 維持拒絕 |
| `gh api repos/a/b`、`gh api -X GET repos/a/b` | 拒絕 | 放行（有效 method 為 GET 且無 `-f/-F/--input`） |
| `gh api … -X POST`、`gh api graphql -f …` | 拒絕 | 維持拒絕 |
| `git st`（本機 config 的一般 alias） | 拒絕 `UNKNOWN_GIT_COMMAND` | 展開後分類；展開成唯讀才放行 |
| alias 展開為 push/commit 或 `!` shell 內含發布 | 拒絕 | 拒絕，新碼 `GIT_ALIAS_PUBLICATION_UNSUPPORTED` |
| `git -c alias.x=push x …` | 拒絕 | 維持拒絕（有 `-c` 時不解析 alias） |
| `git lfs pull/fetch/ls-files/status/track…` | 拒絕 | 放行（唯讀/本機子指令白名單） |
| `git lfs push`、`lock`、`unlock` | 拒絕 | 維持拒絕，新碼 `UNSUPPORTED_GIT_LFS_COMMAND` |
| `git commit -m "$(cat <<'EOF' … EOF\n)"` | 拒絕 | 放行並掃描訊息（僅限引號定界符，且內文不得含定界符行） |
| `git commit -m "$(cat <<EOF …)"`（未加引號） | 拒絕 | 維持拒絕（內文會展開） |
| `git commit -m '用 \`foo\` 修正'`（單引號字面含反引號或 `$`） | 拒絕 | 放行（改用 AST 判斷是否真的有展開） |
| `git add a b && git commit -m …` | 拒絕 | 放行；掃描暫存區 + 即將加入的工作樹檔案 |
| `git commit -a/-am …` | 拒絕 | 放行；掃描所有已追蹤變更的工作樹版本 |
| `git commit --amend -m …`、`--amend --no-edit` | 拒絕 | 放行；掃描暫存區與新訊息 |
| `git commit <pathspec>`、`--only`、`-i`、`-p` | 拒絕 | 維持拒絕（LATER） |
| 只有未追蹤檔時 `git push` / `gh pr create` | 拒絕 `WORKTREE_DIRTY` | 放行；未追蹤路徑仍列在診斷中作提醒 |
| 已追蹤檔有修改/暫存時 push | 拒絕 | 維持拒絕 |
| 命令分類拒絕的 additionalContext | `INTERNAL_DIAGNOSTIC_GAP` | 與拒絕原因相同的穩定碼，含中英文說明 |

## 實作要點

1. `publication_commands.py`
   - 新增「字面 heredoc 替換」前處理：只在非引號、頂層位置辨識 `"$(cat <<'D'\n…\nD\n)"`（含 `<<-`），驗證內文沒有等於定界符的行，再換成等價的單引號字面字串；其他形式維持原本解析。
   - `shell_commands(source, *, mark_dynamic=False)`：預設回傳形狀不變；`mark_dynamic=True` 時以 `\0` 標記真正含展開的字詞，供 commit 檢查區分字面 `$`/反引號與實際展開。
   - 新增 `and_chain(source)`：只接受由 `&&` 串接的簡單指令序列，且沒有其他巢狀指令。
2. `governance_guard.py`
   - `operations_for(command, cwd=None)`：動態全域選項改為「遮罩後分類，結果非空才拒絕」；動態執行檔依字面檔名分類。
   - `_direct_operations`：`gh api` 有效 method 判定；`git lfs` 白名單；alias 以唯讀 `git config --get alias.<verb>` 展開，深度上限 5，存在 `-C/-c/--git-dir/--work-tree/--config-env` 時不解析。
   - `commit_safety`：支援上述形式；把逐檔掃描抽成共用函式，同時處理索引 blob 與工作樹檔案（含大小、媒體、二進位、symlink、submodule 檢查）；未追蹤檔的 injection 判定以全部行為新增行。
   - `hook()`：所有 `CommandError` 都帶穩定 reason code 建立診斷。
3. `publication_authority.py`
   - `PUBLICATION_DIAGNOSTICS` 與 `_ZH` 補上 11 個既有命令分類碼與 2 個新碼。
   - `worktree_dirty_details`：`status` 只看已暫存/已修改/已刪除；新增 `untracked_count`，未追蹤路徑照列。
   - `action()` 改用 `worktree_dirty_details` 判定。
4. `publication_planning.py`：post-merge reconciliation 的乾淨檢查改用相同判定。

## Context / token cost

不新增每輪脈絡、不新增設定。Hook 只有在 Git 動詞不是內建指令時才多執行一次唯讀 `git config`（約數毫秒）。

## Security / reliability

- 受保護發布操作的判定、personal/high-assurance 驗證、secret scan、merge 確認全部不變。
- 放寬只針對「分類結果為非發布」的指令；凡是可能發布的形式仍維持拒絕(fail-closed)。
- `git add && git commit` 改成掃描超集合（暫存區 ∪ 即將加入的工作樹檔），只可能多擋，不會少擋。
- `--amend` 的既有 HEAD 內容在原 commit 時已掃描；push 階段的完整歷史 secret scan 仍然存在。
- 威脅模型照實揭露：hook 防的是誠實 agent 的意外發布，不是對抗式繞過（`python -c` 早已可繞過，這次不處理，屬第 1 項）。
- 未追蹤檔放行的風險：忘記 `git add` 新檔案。緩解：診斷仍列出未追蹤路徑；PR 的 CI 會在乾淨 checkout 上驗證；merge 仍需要必要檢查通過。

## Backward compatibility

- `shell_commands()` 預設回傳形狀不變；新增的參數為可選。
- hook JSON 格式不變；受影響的拒絕改為放行，或拒絕碼變得更精確。
- 以下既有測試的預期會反轉，屬於刻意的行為變更：
  - `test_publication_authority.py` 第 871–872 行：動態 `-C` / `--repo` 搭配唯讀動詞。
  - 第 575 行：`git commit -a`。
  - `test_publication_planning.py` 第 92–98 行：只有未追蹤檔時的 `WORKTREE_DIRTY`（改用已修改的追蹤檔觸發）。
- 已安裝的 runtime（`~/.local/share/aips/system`）要在合併並更新後，live hook 才會套用新行為。

## Scenario / test impact

- 新增正反測試：每一列行為表至少一個放行與一個仍拒絕的案例；heredoc 定界符注入（內文含 `EOF` 行後接 `git push`）必須拒絕；`git add && git commit` 漏掃防護（未暫存的新檔含假密鑰必須擋）。
- 新增契約測試：掃描 `governance_guard.py` 與 `publication_commands.py` 中所有 `CommandError` reason code，必須都在 `PUBLICATION_DIAGNOSTICS` 中，且 hook 診斷碼與拒絕原因一致。
- 更新 Scenario 099（tool guard）、169（content safety publication）、261（diagnostics）。
- 執行：focused 測試 → content-safety / runtime-policy lifecycle → 完整 repository validation → exact-candidate Integration Gate。

## Human docs impact

依 `config/documentation-sync.yaml`，這組檔案會觸發三條規則，要求修改：`docs/ARCHITECTURE.md`、`docs/human/ARCHITECTURE_OVERVIEW.md`、`USER_GUIDE.md`、`TECHNOLOGY_GUIDE.md`、`SECURITY_ASSURANCE.md`、`CONFORMANCE.md`、`INSTALLATION.md`、`MAINTENANCE.md`、`PROJECT_INTELLIGENCE.md`。實質內容只需更新 `USER_GUIDE`（`WORKTREE_DIRTY` 與 commit 形式）、`SECURITY_ASSURANCE`（威脅模型與放寬界線）、`TECHNOLOGY_GUIDE`；其餘只會加一行對應說明以通過閘門（即分析第 9 項的成本）。

## Agent docs impact

規則要求：`orchestration/RESOURCE_AUTHORIZATION.md`、`RUNTIME_POLICY_ENFORCEMENT.md`、`CONFORMANCE.md`、`CONTENT_SAFETY_BOUNDARY.md`、`INTEGRATION_GATE.md`、`CORE_CHANGE_TESTING.md`、`ORCHESTRATOR.md`。實質內容在 `RUNTIME_POLICY_ENFORCEMENT`（分類規則）與 `CONTENT_SAFETY_BOUNDARY`（commit 掃描來源）；`CORE_CHANGE_TESTING` 只加原則性的一句，不寫計畫專屬條款。另外會同步更新全域 harness 文字中「Treat WORKTREE_DIRTY paths as review evidence」的語意（未追蹤檔改為提醒）。

## Architecture diagram impact

N/A。信任邊界與授權流程不變，只調整分類器的判定結果。

## Constitution impact: NO

## Why

不改變 Protected Human Authority、approval 語意、Scope Integrity 或任何受保護操作的放行條件；內容掃描的涵蓋範圍只增不減（撤回 REVIEW 降級後）。

## Recommended AIPS solution

依「實作要點」擴充既有解析器、守衛與診斷表；變更分類為 Core（PR 加 `aips:core-change` 標籤），實作前建立 `.aips/review/CORE_CHANGE_TEST_MATRIX.yaml`，綁定最終 base 與變更檔案雜湊。

## Additional optimization candidates

- LATER：commit 階段 `REVIEW` 降級為警告，前提是 push 階段補上 candidate diff 的 injection 掃描。
- LATER：`gh api graphql` 的唯讀 query 判定。
- LATER：`git commit <pathspec>` / `--only`。
- LATER：放寬 documentation-sync 的「全部文件都要改」規則（分析第 9 項），可大幅降低本次與日後同類變更的文件成本。
- REJECT：在 hook 內實際執行替換或 alias 來判斷結果；或廣泛放行動態發布參數。

以上都不納入本次範圍。

## Expected scope

- 程式：`scripts/publication_commands.py`、`scripts/governance_guard.py`、`scripts/publication_authority.py`、`scripts/publication_planning.py`
- 測試：`tests/test_publication_authority.py`、`tests/test_publication_planning.py`、必要時 `tests/test_publication_diagnostics.py`；Scenario 099 / 169 / 261
- 文件：上列 Human 9 份、Agent 7 份（多數為一行對應說明）
- Core 產物：Core Change Proposal、Core Change Test Matrix
- 預估約 25–30 個檔案，程式實質變更集中在 4 個檔案

## Risks

- heredoc 前處理若判斷錯誤可能造成漏判；以「頂層非引號位置」、「引號定界符」與「內文無定界符行」三重條件，加上注入反例測試來控制。
- `git add && git commit` 的工作樹掃描與實際 `git add` 結果可能有差異（例如 `.gitignore`、`-f`）；不支援的選項一律拒絕，且掃描的是超集合。
- alias 解析讀取 repo 與全域 config；僅唯讀，失敗時回到原本的拒絕。
- 文件閘門強制修改 16 份文件，會讓 diff 變大、審查成本變高。
