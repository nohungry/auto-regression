# Agent Skills 工作流（Skill Pipeline）

> 本文件解釋 `.claude/skills/` 下 6 個 user-invocable skills 的角色分工與接力流程。
> 對象：團隊成員、AI agent（Claude Code）、新進開發者。

## TL;DR

6 個 skill 對應**測試開發生命週期**的 5 個階段 + 1 個旁支：

```
規劃           → 探勘             → 編碼            → 審查         → 提交
pom-architect → selector-probe → ui-test-author → test-review → git-commit
                                                              ↑
                                                env-sync（旁支）
```

**每個 skill 各司其職**，靠 frontmatter 內的「不該觸發」段彼此避讓，
**同一句話最多觸發一個 skill**，不會撞車。

---

## 為什麼有這 6 個 Skill（職責分離原則）

寫測試這件事不是單一動作，而是一個 pipeline：

| 動作 | 需要什麼能力 |
|------|-------------|
| 想清楚 page object 怎麼設計 | 架構思考、跨站 reuse 判斷 |
| 知道實際 DOM 長怎樣 | 瀏覽器操作、ARIA 解讀 |
| 把 selector 寫進 page object | Python / pytest-playwright 慣例 |
| 確認改動沒破壞既有測試 | review 經驗、flaky 偵測 |
| 寫好 commit message 開 PR | git 工作流 |
| 動 .env 不漏站不洩密 | 配置管理紀律 |

把這些**揉進同一個 skill** 會讓那個 skill 太肥、決策標準混亂。
**拆成 6 個專職 skill** 讓每個 skill 的指引精準、實戰 pitfalls 收斂在對的位置。

---

## 各 Skill 角色定位

| 階段 | Skill | 觸發場景（簡） | 不觸發場景 | 下一步通常是 |
|------|-------|--------------|-----------|------------|
| 規劃 | `pom-architect` | 設計新站 POM、跨站 component 抽象、page object 重構 | 已知架構只要寫 selector | `selector-probe` 或 `ui-test-author` |
| 探勘 | `selector-probe` | 找新頁面 selector、debug pytest selector timeout、阻塞 root cause、跨頁對帳 | 要寫 testcase 程式碼、要跑 pytest、要看 Network/React state | `ui-test-author` |
| 編碼 | `ui-test-author` | 寫/改 testcase、寫/改 page object、新站 onboarding | 還不知道 selector（先去 `selector-probe`）、要設計架構（先去 `pom-architect`） | `test-review` 或 `git-commit` |
| 審查 | `test-review` | review PR diff、review flaky 風險、review multi-site 擴展性 | 自己寫的 self-review（直接編輯改） | `git-commit` |
| 提交 | `git-commit` | commit 前檢查、整理 diff、寫 commit message、開 PR | 還在開發中 | merge 後完成 |
| 旁支 | `env-sync` | 動 `.env` / `.env.example` / 合併同事 `.env` 範本 | code 端對接（factory / pages / tests） | `ui-test-author`（如要 onboard 新站） |

完整 trigger 規則寫在每個 skill 的 frontmatter `description` 與內文的「Trigger」段。

---

## 真實任務範例（看 skill 怎麼依序接力）

### 範例 1：LT 改版後 `pages/lt/home_page.py` 整套失效，要重寫

```
你：「LT 又改版了，home_page.py 全套 selector 都過時，請重寫」

階段 1：架構決策
  → pom-architect：「新版 LT 是桌面 responsive WAP，drawer 結構變了，
                    home_page 要不要拆成 home_page + drawer_component？」

階段 2：實際 selector probe
  → selector-probe：用 agent-browser snapshot LT 首頁 + drawer 開關後狀態，
                    拿出新版實際 className（如 .login-btn-with-text 取代 .bg-navbar）

階段 3：重寫 page object
  → ui-test-author：把 probe 出來的 selector 寫進新 home_page.py，
                    遵守 CLAUDE.md 的 selector 規則（不綁文案、避開 pitfalls）

階段 4：跑 pytest 驗證
  → 直接 .venv/bin/pytest tests/lt/test_p0_smoke.py（不用 skill，這是 bash）

階段 5：自我 review
  → test-review：「我寫的 home_page.py 有沒有 flaky 風險？」

階段 6：提交
  → git-commit：「整理 diff 寫 commit message」
```

→ **6 個階段最多用 4 個 skill**（pom-architect / selector-probe / ui-test-author / git-commit），不會混亂。

---

### 範例 2：dev-rc 出新蓋板廣告擋住測試

```
你：「dev-rc 又有新蓋板擋住登入按鈕，pytest 全 fail」

階段 1：probe 蓋板結構
  → selector-probe：snapshot dev-rc 首頁，拿到蓋板 mask + 關閉按鈕的 className，
                    試 dispatchEvent 確認可關閉

階段 2：寫 dismiss helper
  → ui-test-author：把 selector 寫進 utils/dialog_helper.py 的
                    dismiss_overlay_ad_if_present()，掛到 LoginPage.goto() 與
                    tests/rc/conftest.py 的 go_home

階段 3：跑 pytest 驗證
  → 直接 .venv/bin/pytest tests/rc/test_p0_smoke.py

階段 4：提交
  → git-commit
```

→ **沒用到 pom-architect**（架構不變）、**沒用到 test-review**（小改動自己 review）。

---

### 範例 3：新增第 9 個站（如 ABC 站）

```
你：「新增 ABC 站，先把 .env 對齊，code 之後再接」

階段 1：.env keys 對齊
  → env-sync：在 .env 與 .env.example 兩處同步加 SITE_ABC_* 12 keys，
              照站台命名 quirks 規則

階段 2：（之後）等實際要 onboard 時
  → pom-architect → selector-probe → ui-test-author 依序接力

階段 3：提交
  → git-commit
```

→ **不要在 .env 加 keys 後馬上跳到 code 端**，env-sync skill 會明確提醒「code 端尚未接，跑該站會 raise ValueError」。

---

## 為什麼不會衝突（避讓機制）

每個 skill 的 frontmatter `description` + 內文的「不該觸發此 skill」段，
**互斥地**列出該 skill 不負責的場景，並指向正確的 skill。

例如 `selector-probe` 的避讓條款：

```markdown
# 不該觸發此 skill
- 使用者要寫 testcase 程式碼 → 用 ui-test-author
- 使用者要設計 page object 結構 → 用 pom-architect
- 使用者要跑回歸測試 / 跑 pytest → 直接用 .venv/bin/pytest
- 使用者要寫 commit / 開 PR → 用 git-commit
- 使用者要改 .env → 用 env-sync
- 使用者要看 Network waterfall / response body → chrome-devtools MCP
- 使用者要看 React component state / props → chrome-devtools MCP + React DevTools
- 使用者要錄完整使用者操作影片 / trace → playwright MCP
```

→ **同一句話 Claude 最多選一個 skill 跑**，不會兩個並行。
→ 跨階段任務（如「LT POM 重寫」）會**依序**觸發多個 skill。

---

## Skill 與外部工具的分工

不是所有事都該用這 6 個 skill 解，有些要交給外部 MCP：

| 場景 | 用什麼 |
|------|--------|
| 看 Network 請求 / response body | chrome-devtools MCP |
| 看 React component state / props | chrome-devtools MCP + React DevTools |
| 錄製完整使用者操作 trace | playwright MCP |
| 跑 lighthouse / a11y audit | chrome-devtools MCP |
| 簡單 selector probe / ARIA tree | **selector-probe**（用 agent-browser CLI） |
| 跨頁面數據對帳 | **selector-probe** Pattern D |

`selector-probe` 補強了 chrome-devtools MCP 在「**輕量探勘**」場景的不足
（CLI 一行就拿 ARIA tree，比 MCP 多輪 tool call 輕）。

---

## Subagent 層（main agent 自動派工）

除了**人類**透過 `/skill-name` 觸發 skill，repo 也有 **main agent** 可主動 delegate 的 subagent，位於 `.claude/agents/<name>.md`。Subagent 解決 skill 解不了的痛點：

| 維度 | Skill | Subagent |
|------|-------|----------|
| 觸發者 | 人類 `/skill-name` | Main agent 自主判斷 |
| 執行 context | 主對話內 | **獨立 context window** |
| 工具權限 | 繼承主對話 | 自帶白名單（可限縮） |
| 典型用途 | 流程指引、規則文件 | 並行調查、髒活隔離、大量檔案讀取 |
| 回傳 | 對話延續 | 一段 summary 字串 |

簡單講：**skill = 主對話的指引；subagent = 主對話派出去辦事的小弟，回來只交報告**。

### 目前有的三個 subagent

| Subagent | Inject 的 skill | 工具 | 主要職責 |
|---------|---------------|------|---------|
| `test-author` | `ui-test-author`、`pom-architect` | Read, Write, Edit, Bash, Grep, Glob | 新增/修改 testcase、POM、實作功能驗證 |
| `test-reviewer` | `test-review` | Read, Grep, Glob, Bash | Read-only review、找 flaky / cover-up / 跨站風險 |
| `selector-explorer` | `selector-probe` | Read, Grep, Glob, Bash | DOM 探查、ARIA 拿 selector、被蓋板擋住的 debug |

三 agent **互不能 spawn 對方**（都沒 Agent tool），handoff 一律繞回主對話決定下一步。

### 三 agent 接力 SOP

**情境 A：使用者要新增 RC 新功能測試（例如錢包頁）**

```
使用者：「幫我加 RC 錢包頁的測試」

階段 1：main agent 派 selector-explorer 探 DOM
  → 回報 selector + 給 test-author 的可用片段

階段 2：main agent 派 test-author 實作
  → 寫 POM + testcase，跑 .venv/bin/pytest tests/rc/feature/wallet/
  → 回報變更檔案 + pytest 結果

階段 3：main agent 派 test-reviewer 審查
  → read-only review，列 blocking / non-blocking

階段 4：main agent 自走 git-commit skill 開 PR
```

**情境 B：既有測試突然 fail（不確定 root cause）**

```
階段 1：main agent 派 test-reviewer 看 fail trace + git log + 截圖
  → 回報 root cause 假設

階段 2：依 root cause 派下一步
  - selector 過時 → 派 selector-explorer 重 probe
  - 產品 regression → **回報使用者**（不要派 test-author 修，會掩蓋 regression）
  - 測試自身 bug → 派 test-author 修

階段 3：修完派 test-reviewer 二審 → 主對話走 git-commit
```

→ **debug 既有 fail 不要派 test-author**（test-author 的 description 已明示）。

**情境 C：新增第 9 個站（前台 + 後台 + API 全套）**

```
階段 1：主對話走 env-sync skill 同步 .env
階段 2：main agent 派 selector-explorer 探 ABC 前台 / 後台 DOM
階段 3：main agent 派 test-author 寫前台 POM / smoke + 後台 POM / smoke + API conftest
階段 4：main agent 派 test-reviewer 審 onboarding 完整性（A/B/C 三分支）
階段 5：主對話走 git-commit
```

### 避讓機制（subagent vs skill）

兩者的差別不在「該不該存在」而在「**誰負責觸發**」：

- 使用者**明確**輸入 `/skill-name` → 走 skill 模式（主對話內執行）
- 使用者**隱性**要求「幫我做 X」→ main agent 看 X 屬於哪個 subagent 的職責，主動 delegate
- 衝突情境（例如使用者輸入 `/ui-test-author` 但 Claude 認為該派 `test-author`）→ **尊重使用者明示意圖**，走 skill 模式

Subagent 三人之間靠 description 與「不在你的職責內」段互斥，handoff 透過主對話橋接（subagent A 想交給 subagent B 時，回報主對話「請改派 B」，由主對話決定）。

---

## 工作流會演化

這 6 個 skill 不是固定的，會隨實戰需求**加 / 拆 / 合併**：

- **加新 skill**：碰到反覆出現的工作流模式（例如未來要加 `dashboard-rollback`、`api-contract-test`）
- **拆現有 skill**：某個 skill 變太肥（例如 `ui-test-author` 未來可能拆成 `testcase-author` + `page-object-author`）
- **合併**：兩個 skill 職責漸趨重疊時

判斷原則：**Skill 的 ROI 在於「給 Claude 與人類一個明確的工作 context」**。當一個 skill 內容不再聚焦（既要做 A 又要做 B），就該拆。當兩個 skill 經常一起被觸發（總是同時用），就該考慮合併。

新增 / 修改 skill 時：
1. 同步更新 `CLAUDE.md` 的 Agent Skills 表格
2. 同步更新本文件（角色定位表、範例、避讓條款）
3. 在 PR 描述說明「為什麼這個 skill 該獨立存在」

---

## 相關文件

- `CLAUDE.md` 的 `## Agent Skills` 段 — repo 層級的 skill 索引
- `.claude/skills/<name>/SKILL.md` — 各 skill 的詳細指引（trigger、workflow、pitfalls、紅線）
- `dev-notes/agent-browser-spike-2026-05-02.md` — selector-probe skill 的設計 spike 經過
- `dev-notes/agent-browser-cookbook.md` — selector-probe 對應的 agent-browser 命令備忘
