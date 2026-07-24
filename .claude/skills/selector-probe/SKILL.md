---
name: selector-probe
description: 找新頁面 selector、debug pytest selector timeout、排除蓋板/彈窗阻塞、確認 dev 環境當前 DOM 結構時，用 agent-browser CLI 即時 probe ARIA accessibility tree。補強 chrome-devtools MCP 在「寫測試前的探勘」與「pytest 失敗 root cause 分析」場景。觸發詞：selector 找不到、找不到按鈕、Locator timeout、新蓋板擋住、dev 環境改了什麼、頁面結構是什麼、跨頁面數字對不上。
---

# Purpose

在 auto-regression repo 中，扮演「**寫測試之前的探勘工具**」與「**pytest 失敗時的 DOM root cause 分析工具**」。

agent-browser 是 Vercel 出的 Rust CLI，特性：
- 一行 bash 即可拿到 ARIA accessibility tree（比 raw HTML 易讀）
- 走 CDP 連 Windows Chrome 9223，與 pytest 共用 browser
- 互動式操作（snapshot / click / eval），不寫進測試碼
- 支援 batch 指令一次抓多頁，適合跨頁面數據比對

# Trigger（何時觸發）

主動偵測以下情境並使用：

1. 使用者問**新頁面的 selector** 不知道在哪（特別是 React SPA、動態渲染頁）
2. 使用者貼出 pytest 的 `Locator.wait_for: Timeout` / `element not found` / 「找不到 XXX 按鈕」錯誤
3. 使用者描述 dev 環境出現**新蓋板 / 新彈窗 / 廣告 / dialog** 擋住測試
4. 使用者要**比對「測試以為的 DOM」vs「實際 DOM」**
5. 使用者問「LT 改版後 `xxx` 還在嗎」「dev-rc 蓋板廣告長怎樣」這種**現況確認**問題
6. 使用者要做**跨頁面數字對帳**（前端 vs 後端、會員 vs 代理視角）— 走 Pattern D
7. 上述場景中，使用者沒明確指定工具時 — **預設用 agent-browser**（取代以前預設 chrome-devtools MCP 的選擇）

# 不該觸發此 skill

- 使用者要**寫 testcase 程式碼** → 用 `ui-test-author`
- 使用者要**設計 page object 結構** → 用 `pom-architect`
- 使用者要**跑回歸測試 / 跑 pytest** → 直接用 `.venv/bin/pytest`
- 使用者要**寫 commit / 開 PR** → 用 `git-commit`
- 使用者要**改 .env** → 用 `env-sync`
- 使用者要**看 Network waterfall / response body** → chrome-devtools MCP
- 使用者要**看 React component state / props** → chrome-devtools MCP + React DevTools
- 使用者要**錄完整使用者操作影片 / trace** → playwright MCP

# 與 chrome-devtools MCP 的分工

兩者功能重疊但取捨不同：

| 維度 | chrome-devtools MCP | agent-browser |
|------|---------------------|---------------|
| 啟動成本 | MCP server 必須連線 | CLI 一行 |
| 輸出格式 | raw DOM / JS console | ARIA tree（語意化） |
| 互動方式 | 多輪 tool calls | 單行 bash 指令 |
| 跨頁面 batch | 多次 tool call | 單次 batch 指令 |
| 適合場景 | 需要 React DevTools / Network panel 等深度 debug | 快速 selector probe / snapshot 比對 / 跨頁對帳 |

**預設先用 agent-browser**，需要 Network / React state 才退回 chrome-devtools MCP。

# Setup（首次使用前）

```bash
# 安裝（用 nvm 不需 sudo）
npm install -g agent-browser@<已驗證的版本>

# 連 Windows Chrome 9223（每次新 shell 要重連；CDP_URL 讀 .env，勿硬編 IP）
CDP_URL=$(grep -E '^CDP_URL=' .env | cut -d= -f2)
WS=$(curl -s "$CDP_URL/json/version" | python3 -c 'import sys,json; print(json.load(sys.stdin)["webSocketDebuggerUrl"])')
agent-browser connect "$WS"

# 檢查當前版本
agent-browser --version
```

> 升級前先看 changelog；agent-browser 還在快速迭代，breaking change 機率不低。

詳細命令範例見 `dev-notes/agent-browser-cookbook.md`。

# Output 管理（避免 context 爆量）

snapshot 在複雜頁面（例如 LT 首頁帶遊戲列表）輸出可能上千行，直接餵給對話會吃掉大量 context。**通則：先寫到檔案 + grep，不要直接把全部 snapshot 塞進對話**。

控制輸出量的手法：

- 寫檔案不直接讀：`agent-browser snapshot > /tmp/probe.txt`，然後 `grep` / `head` 取需要片段
- selector scope：`agent-browser snapshot -s "#main-nav"` 只看特定區塊
- interactive only：`agent-browser snapshot -i` 只取 button / link / input
- depth 限制：`agent-browser snapshot -d 3` 限制 ARIA tree 深度
- compact 模式：`agent-browser snapshot -c` 移除空的結構性節點
- 組合使用：`agent-browser snapshot -i -c -d 5 -s "#content"`

# Workflow（依場景分）

## Pattern A：新頁面 selector probe

1. `agent-browser open <url>` 進站
2. **必等 SPA hydration 完成**（dev-rc / dev-lt 至少 3~5 秒）：
   ```bash
   sleep 3
   agent-browser wait --fn "document.querySelectorAll('nav, [role=navigation], header').length > 0"
   ```
   雙保險：固定 sleep 打底 + 條件 wait 等 navbar/header 出現。**不要用 `wait --load networkidle`**（dev 環境心跳 WS 永不 idle）。
3. `agent-browser snapshot -i -c > /tmp/probe.txt` 拿 interactive ARIA tree
4. 從 tree 找目標元素的 `[ref=eN]`
5. `agent-browser eval` 拿 className / parent 結構（不要直接信 ARIA tree 的標籤，要核對真實 className）
6. 把 className 寫進 `pages/<site>/<page>.py` 的 locator
7. 寫 testcase / 修 page object（轉 `ui-test-author`）

## Pattern B：debug pytest 失敗

1. 看 pytest stack trace 找出 timeout / not found 的 selector
2. **判斷目標頁是否需要登入後 state**：
   - 公開頁（login / 公告）→ 直接 `open <URL>`
   - 登入後頁（會員中心 / 投注記錄 / 玩家合計）→ 先確認 Chrome 9223 已是登入狀態
     - 用 `agent-browser eval "document.cookie"` 確認有 session cookie
     - 或先 `agent-browser open <login_url>` 手動登入一次，後續 probe 共用 session
   - **若沒做這步，probe 會被導去 login 頁**，拿到的 ARIA tree 是錯的
3. `agent-browser open <該頁 URL>` + sleep 3 + wait condition（同 Pattern A 第 2 步）
4. `agent-browser snapshot > /tmp/probe.txt && grep -i "<目標關鍵字>" /tmp/probe.txt` 看實際 DOM 有什麼
5. 對照「pytest 期待」vs「實際存在」找差異
6. 修 page object selector → 跑 pytest 驗證

## Pattern C：阻塞 / 蓋板 root cause

1. `agent-browser open <被擋的頁面>` + sleep 3 + wait condition
2. `agent-browser snapshot -d 3 | head -30` — 蓋板通常在頂端 ARIA 區塊
3. 找 `button "✕" / "關閉" / "略過"` 等 ref
4. `agent-browser eval` 看蓋板 mask 的 z-index / position / className（蓋板通常 `position:fixed; z-index:9999+`）
5. **預設走 dispatchEvent（最保險，跳過試錯）**：
   ```bash
   agent-browser eval '(() => {
     const el = document.querySelector(".close-circle-btn");
     if (!el) return "not found";
     el.dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true, view: window}));
     return "dispatched";
   })()'
   ```
   理由：`agent-browser click @eN` 在 React 17+ synthetic event 系統下不一定會被 handler 接到。
   `dispatchEvent(new MouseEvent("click", {bubbles: true}))` 會走 React 的 event delegation，
   通常都能觸發。直接用這條路徑省去「先試失敗再 fallback」的 round trip。

   ⚠️ 不要用 `getEventListeners()` 檢查 listener — 那是 Chrome DevTools console 專用 API，
   `agent-browser eval` 在 page context 跑沒這個 function（spike 2026-05-02 實測）。

   若 dispatchEvent 也沒效，依序試：
   - 元素被 mask 攔 pointer-events → eval 把 mask `style.pointerEvents = "none"` 暫時讓 mask 不擋
   - 真實 handler 綁在父元素 → 改用 `el.parentElement.dispatchEvent(...)`
   - 還是不行 → 蓋板可能本來就不該關（產品設計），跟使用者確認後再寫 helper
6. 確認可靠關閉路徑後，寫進 `utils/dialog_helper.py` 的 helper

## Pattern D：跨頁面數據 sanity check（前後端對帳場景）

當需要快速比對「同一筆數據在不同頁面/角色看到的數字」（常見於洗碼佣金、代理拆帳、流水報表）：

1. 確認兩邊都已登入（會員 + agent / 後台 superuser）— 同 Pattern B 第 2 步
2. 用 `batch` 一次抓兩個頁面的數字區塊：
   ```bash
   agent-browser batch \
     '["open", "<frontend_revenue_url>"]' \
     '["wait", "--fn", "document.querySelector(\"#totalRevenue\")"]' \
     '["snapshot", "-s", "#totalRevenue", "--json"]' \
     '["open", "<backend_player_total_url>"]' \
     '["wait", "--fn", "document.querySelector(\"#playerTotal\")"]' \
     '["snapshot", "-s", "#playerTotal", "--json"]' > /tmp/cross.json
   ```
3. 把 `/tmp/cross.json` 餵給對話做數字比對 + 捨入策略推測
4. 確認差異原因後，**再決定是否寫成正式 cross-source consistency test**
   （寫測試的話走 `ui-test-author`，放進 `tests/api/<site>/`）

> 注意：probe 階段先確認**邏輯是否真的有 bug**，不要倒過來先寫測試再 probe（浪費）。

# Session reset（當懷疑狀態被污染時）

Chrome 9223 是共用 session，agent-browser 用 default tab，會繼承上次 cookie / state。當 probe 結果反常時：

```bash
# 清 cookie + reload
agent-browser cookies clear
agent-browser reload

# 或更徹底：close 後重連（CDP_URL 讀 .env）
agent-browser close
CDP_URL=$(grep -E '^CDP_URL=' .env | cut -d= -f2)
WS=$(curl -s "$CDP_URL/json/version" | python3 -c 'import sys,json; print(json.load(sys.stdin)["webSocketDebuggerUrl"])')
agent-browser connect "$WS"
```

# 安全紅線（必守）

1. **agent-browser 命令永不寫進 `tests/` 或 `pages/`** — pytest 跑回歸不該依賴外部 CLI 是否存在
2. **不要用 chat 模式跑 regression** — non-deterministic，污染 baseline
3. **不要在 CI 安裝 agent-browser** — CI 用 pytest 就夠
4. **不要拿 agent-browser 取代 pytest** — 它沒 fixture / report / parameterize / xfail
5. **probe 時帳密一律走 env var，不直接打進命令列**
   - 帳號可以（留在 history 沒關係）
   - 密碼**必走** `$DRC_PASSWORD` / `$LT_PASSWORD`（從 `.env` source）
   - 範例：`agent-browser fill @e3 "$DRC_PASSWORD"`（注意要雙引號讓 shell 展開）
   - 原因：shell history、tmux scrollback、screen recording 都會洩漏明文密碼

# 已知 pitfalls（spike 2026-05-02 學到）

1. **`agent-browser click @eN` 不一定觸發 React event** — 部分 React app 用 synthetic event，native click 沒效。Workaround：用 eval `dispatchEvent(new MouseEvent("click", {bubbles: true}))`
2. **`is visible` 兩種視角會不一致** — playwright `is visible`（含 viewport intersection / opacity）vs CSS `display !== "none"` 可能矛盾。debug 用 eval 看 computed style 比 `is visible` 可靠
3. **dev-rc / dev-lt SPA hydration 至少 3~5 秒** — `wait --load networkidle` 不可靠（dev 環境心跳 WS 永不 idle），用 sleep + 條件 wait 雙保險
4. **Chrome 9223 是共用 session** — agent-browser 用 default tab，會繼承上次 cookie / state；不確定狀態時走「Session reset」段
5. **dev 環境蓋板表現飄忽** — 同一頁面多次 reload 蓋板可能時有時無，不要靠單次 probe 下結論
6. **登入後頁面直接 open 會被踢回 login** — 走 Pattern B 第 2 步先確認 session

# 與其他 skill / 工具的銜接

| 完成 probe 後可能下一步 | 對應工具 |
|------------------------|---------|
| 把 selector 寫進 page object | `ui-test-author` |
| 重構 page object 結構 | `pom-architect` |
| 改完 page object 後跑 pytest 驗證 | 直接 `.venv/bin/pytest tests/<site>/...` |
| review 測試改動 | `test-review` |
| commit / 開 PR | `git-commit` |

# 何時應該放棄 agent-browser、改用其他工具

- 需要看 Network waterfall / response body → chrome-devtools MCP
- 需要看 React component state / props → chrome-devtools MCP + React DevTools
- 需要錄製完整使用者操作影片 → playwright MCP 的 trace
- 需要跑 lighthouse / a11y audit → chrome-devtools MCP 的 lighthouse_audit
- probe 超過 5 次還沒找到 selector → 停下來，可能是頁面真的還在開發中，或 selector 在 shadow DOM / iframe 裡

# 相關檔案

- `dev-notes/agent-browser-cookbook.md` — 個人命令備忘（gitignored）
- `dev-notes/agent-browser-spike-2026-05-02.md` — 工具評估實驗報告
- `utils/dialog_helper.py` — 蓋板 / 彈窗 dismiss helpers（probe 出來的 selector 寫進這）

# cookbook 應收錄哪些片段

未來累積到 `dev-notes/agent-browser-cookbook.md` 的內容建議包含：

- React synthetic event 的 `dispatchEvent` 完整寫法（含 bubbles / cancelable / composed 設定）
- 各站台登入腳本（用 env var、不寫死密碼）
- 蓋板 dismiss 經典案例（每次 probe 出新的就累積進來）
- batch 指令的 JSON 格式範本（含 wait + snapshot + open 組合）
- snapshot scope / filter 的常用組合（按站台、按頁面分類）
- Pattern D 的對帳 batch 範本（依不同報表頁面）
