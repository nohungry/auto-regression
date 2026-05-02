---
name: selector-probe
description: 用 agent-browser CLI 即時 probe 網頁 selector / ARIA 結構，補強 chrome-devtools MCP 在「寫測試前的探勘」與「pytest 失敗 root cause 分析」場景。當使用者要找新頁面 selector、debug pytest selector timeout、排除蓋板/彈窗阻塞、或想快速看 dev 環境某頁面的 DOM 結構時，使用此 skill。
---

# Purpose

在 auto-regression repo 中，扮演「**寫測試之前的探勘工具**」與「**pytest 失敗時的 DOM root cause 分析工具**」。

agent-browser 是 Vercel 出的 Rust CLI，特性：
- 一行 bash 即可拿到 ARIA accessibility tree（比 raw HTML 易讀）
- 走 CDP 連 Windows Chrome 9223，與 pytest 共用 browser
- 互動式操作（snapshot / click / eval），不寫進測試碼

# Trigger（何時觸發）

主動偵測以下情境並使用：

1. 使用者問**新頁面的 selector** 不知道在哪（特別是 React SPA、動態渲染頁）
2. 使用者貼出 pytest 的 `Locator.wait_for: Timeout` / `element not found` / 「找不到 XXX 按鈕」錯誤
3. 使用者描述 dev 環境出現**新蓋板 / 新彈窗 / 廣告 / dialog** 擋住測試
4. 使用者要**比對「測試以為的 DOM」vs「實際 DOM」**
5. 使用者問「LT 改版後 `xxx` 還在嗎」「dev-rc 蓋板廣告長怎樣」這種**現況確認**問題
6. 上述場景中，使用者沒明確指定工具時 — **預設用 agent-browser**（取代以前預設 chrome-devtools MCP 的選擇）

# 不該觸發此 skill

- 使用者要**寫 testcase 程式碼** → 用 `ui-test-author`
- 使用者要**設計 page object 結構** → 用 `pom-architect`
- 使用者要**跑回歸測試 / 跑 pytest** → 直接用 `.venv/bin/pytest`
- 使用者要**寫 commit / 開 PR** → 用 `git-commit`
- 使用者要**改 .env** → 用 `env-sync`

# 與 chrome-devtools MCP 的分工

兩者功能重疊但取捨不同：

| 維度 | chrome-devtools MCP | agent-browser |
|------|---------------------|---------------|
| 啟動成本 | MCP server 必須連線 | CLI 一行 |
| 輸出格式 | raw DOM / JS console | ARIA tree（語意化） |
| 互動方式 | 多輪 tool calls | 單行 bash 指令 |
| 適合場景 | 需要 React DevTools / Network panel 等深度 debug | 快速 selector probe / snapshot 比對 |

**預設先用 agent-browser**，需要 Network / React state 才退回 chrome-devtools MCP。

# Setup（首次使用前）

```bash
# 安裝（用 nvm 不需 sudo）
npm install -g agent-browser

# 連 Windows Chrome 9223（每次新 shell 要重連）
WS=$(curl -s http://172.30.80.1:9223/json/version | python3 -c 'import sys,json; print(json.load(sys.stdin)["webSocketDebuggerUrl"])')
agent-browser connect "$WS"
```

詳細命令範例見 `dev-notes/agent-browser-cookbook.md`。

# Workflow（依場景分）

## Pattern A：新頁面 selector probe

1. `agent-browser open <url>` 進站
2. **必 sleep 5+ 秒**（dev-rc / dev-lt SPA hydration 慢，過早 snapshot 拿不到 navbar）
3. `agent-browser snapshot > /tmp/probe.txt` 拿 ARIA tree
4. 從 tree 找目標元素的 `[ref=eN]`
5. `agent-browser eval` 拿 className / parent 結構（不要直接信 ARIA tree 的標籤，要核對真實 className）
6. 把 className 寫進 `pages/<site>/<page>.py` 的 locator
7. 寫 testcase / 修 page object（轉 `ui-test-author`）

## Pattern B：debug pytest 失敗

1. 看 pytest stack trace 找出 timeout / not found 的 selector
2. `agent-browser open <該頁 URL>` + sleep 5
3. `agent-browser snapshot | grep -i "<目標關鍵字>"` 看實際 DOM 有什麼
4. 對照「pytest 期待」vs「實際存在」找差異
5. 修 page object selector → 跑 pytest 驗證

## Pattern C：阻塞 / 蓋板 root cause

1. `agent-browser open <被擋的頁面>` + sleep 5
2. `agent-browser snapshot | head -30` — 蓋板通常在頂端 ARIA 區塊
3. 找 `button "✕" / "關閉" / "略過"` 等 ref
4. `agent-browser eval` 看蓋板 mask 的 z-index / position / className（蓋板通常 `position:fixed; z-index:9999+`）
5. 試 `agent-browser click @eN` 看蓋板會不會消
6. **若 click 沒效**（React event handler 沒走到），用 eval 手動 dispatch click event（見 cookbook 「pitfalls」段）
7. 確認可靠關閉路徑後，寫進 `utils/dialog_helper.py` 的 helper

# 安全紅線（必守）

1. **agent-browser 命令永不寫進 `tests/` 或 `pages/`** — pytest 跑回歸不該依賴外部 CLI 是否存在
2. **不要用 chat 模式跑 regression** — non-deterministic，污染 baseline
3. **不要在 CI 安裝 agent-browser** — CI 用 pytest 就夠
4. **不要拿 agent-browser 取代 pytest** — 它沒 fixture / report / parameterize / xfail
5. **probe 時不要用真實密碼** —（agent-browser 命令會留在 shell history）；測試帳號可，但密碼避免直接打進命令列，必要時用 env var

# 已知 pitfalls（spike 2026-05-02 學到）

1. **`agent-browser click @eN` 不一定觸發 React event** — 部分 React app 用 synthetic event，native click 沒效。Workaround：用 eval `dispatchEvent(new MouseEvent("click", {bubbles: true}))`
2. **`is visible` 兩種視角會不一致** — playwright `is visible`（含 viewport intersection / opacity）vs CSS `display !== "none"` 可能矛盾。debug 用 eval 看 computed style 比 `is visible` 可靠
3. **dev-rc / dev-lt SPA hydration 至少 3~5 秒** — `wait --load networkidle` 不可靠（dev 環境心跳 WS 永不 idle），用 sleep
4. **Chrome 9223 是共用 session** — agent-browser 用 default tab，會繼承上次 cookie / state；不確定狀態時 reload 或清 cookie
5. **dev 環境蓋板表現飄忽** — 同一頁面多次 reload 蓋板可能時有時無，不要靠單次 probe 下結論

# 與其他 skill / 工具的銜接

| 完成 probe 後可能下一步 | 對應工具 |
|------------------------|---------|
| 把 selector 寫進 page object | `ui-test-author` |
| 重構 page object 結構 | `pom-architect` |
| 改完 page object 後跑 pytest 驗證 | 直接 `.venv/bin/pytest tests/<site>/...` |
| review 測試改動 | `test-review` |
| commit / 開 PR | `git-commit` |

# 相關檔案

- `dev-notes/agent-browser-cookbook.md` — 個人命令備忘（gitignored）
- `dev-notes/agent-browser-spike-2026-05-02.md` — 工具評估實驗報告
- `utils/dialog_helper.py` — 蓋板 / 彈窗 dismiss helpers（probe 出來的 selector 寫進這）
