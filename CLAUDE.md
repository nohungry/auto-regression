# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

End-to-end regression test suite for a gaming platform (T9 Platform) using Python + pytest-playwright. Tests run against a live site via a Chrome browser, either locally or via CDP (Chrome DevTools Protocol) when running from WSL.

## Setup

```bash
cp .env.example .env   # Fill in credentials and CDP_URL
pip install -r requirements.txt
playwright install chromium
```

Key `.env` variables:
- `DEFAULT_SITE` — which site config to use (e.g. `rc`)
- `CDP_URL` — Chrome remote debug URL (WSL/Linux only; e.g. `http://<WINDOWS_IP>:9223`)
- `SITE_<NAME>_URL/USERNAME/PASSWORD` — per-site credentials

## Running Tests

**Always use the project's virtualenv** located at `.venv/`:

```bash
.venv/bin/pytest                                                        # all tests
.venv/bin/pytest tests/rc/                                             # rc site only (no --site needed)
.venv/bin/pytest tests/lt/                                             # lt site only (no --site needed)
.venv/bin/pytest tests/lt/test_p0_smoke.py -m p0                         # lt p0 smoke tests
.venv/bin/pytest -m p0                                                  # by marker
.venv/bin/pytest -m login                                               # by marker
.venv/bin/pytest tests/rc/test_p0_smoke.py::TestLogin::test_login_success # single test
CI=true .venv/bin/pytest tests/rc/test_p0_smoke.py                      # 模擬 CI 模式：headless chromium 直接 launch（無 CDP）
```

Reports are written to `reports/report.html` (self-contained HTML).

## CI/CD

GitHub Actions 自動跑測試：

- `p0.yml`：PR 開啟 / push to main / 每天 09:00 台灣 / 手動 → RC + LT + RE + RD + QW P0 smoke 5 站 matrix
- `full-regression.yml`：每週一 08:00 台灣 / 手動 → 5 站全套（P0 + feature）
- `docs-sync-check.yml`：PR 時檢查 code 變動是否有對應 .md 更新（hook 機制 + CI 雙保險）

詳細的 trigger 規則、cron 時段、secrets 清單、如何看 run / 下載 artifact / 加 secret / debug fail → 見 [`docs/cicd.md`](docs/cicd.md)。

## Docs sync check（hook + CI 雙保險）

每次 commit / PR 自動檢查「code 變動是否同步更新 docs」：

- **Hook**（`.claude/settings.json` + `.github/scripts/check-docs-sync.sh`）：Claude 在跑 `git commit` 之前 block，stderr 提醒重看哪些 .md
- **CI**（`.github/workflows/docs-sync-check.yml`）：PR 時相同檢查跑一次，違規 → PR check 紅

確認**不**需要更新時的 override：
- commit message 加 sentinel `[skip-docs-check]` 並附理由
- 或設 env var `SKIP_DOCS_CHECK=1`

## Test Strategy

| 測試類型 | Fixture | Scope | 適用情境 |
|---------|---------|-------|---------|
| Smoke | `page` | function | 每次測試獨立 context，各自登入登出。驗證核心流程（登入/登出/首頁元素）。LT smoke 不使用 `logged_in_page`，避免 fixture 的 drawer 開關汙染截圖流程。 |
| Functional | `class_logged_in_page` + `go_home` | class | 一個 class 只登入一次，測試間共用 session，`go_home` 每個測試前回首頁。適合功能驗證。 |

各站點測試放在 `tests/<site_id>/` 下；smoke 測試統一命名 `test_p0_smoke.py`，功能型測試放 `tests/<site_id>/feature/<feature_name>/`。

## 測試結果判讀（Result Interpretation）

當測試失敗時，先區分「測試問題」還是「真實 FAIL」：

1. **檢視流程**：照截圖逐步確認 selector 命中、按鈕被按到、API 真的有送出 — 是否走完原本設計的 happy path？
2. **若流程無異常但結果非預期**（例如：點擊都成功但畫面顯示「連線失敗」、API 回傳錯誤碼、後續驗證找不到應有資料），**判定為真實 FAIL，不可加 `@pytest.mark.skip` 掩蓋**。
3. 真實 FAIL 通常代表**被測站點本身有 regression**（後端服務改動、產品 bug、資料配置壞掉）— 測試的職責就是揪出這個訊號。
4. 只有當問題明確屬於**測試自身**（selector 過時、timing race、test data 失效）才修測試碼或加 skip + 完整理由。

> 反例：dev-rc 遊戲 spin 後顯示「連線失敗 - 錯誤代碼 5305」，按鈕都點對了、API 也送了 — 這是 RD 改動造成遊戲後端壞掉的 regression FAIL，不該為了讓 CI 綠燈而 skip 該 test。

## Architecture

```
conftest.py                  — browser setup, environment detection (Windows/WSL/Linux), global fixtures
config/settings.py           — multi-site SiteConfig dataclass loaded from .env
pages/factory.py             — frontend: routes site_id → LoginPage/HomePage class via registry dict (no if/else fallback; unknown site_id raises ValueError)
pages/dashboard/factory.py   — backend dashboard: routes site_id → DashboardLoginPage/ManagementPage class (independent registry from frontend; no cross-import)
pages/rc/                   — rc site Page Objects (LoginPage, HomePage) — 王老吉娛樂城
pages/lt/                   — lt site Page Objects (LoginPage, HomePage) — LT來財
pages/re/                   — re site Page Objects (LoginPage, HomePage) — BeWin
pages/rd/                   — rd site Page Objects (LoginPage, HomePage) — 狗狗娛樂城
pages/qw/                   — qw site Page Objects (LoginPage, HomePage) — LM來財娛樂城（Nuxt/Vue，多語系）
pages/dashboard/<site_id>/   — backend dashboard page objects (DashboardLoginPage, ManagementPage); per dashboard factory registry
tests/api/<site_id>/         — API-layer tests (requests only, no browser, no pages/* import); per-site conftest
tests/dashboard/<site_id>/   — backend dashboard tests; state-mutating tests should be reversible (rollback / teardown compensation)
tests/rc/                   — rc site tests (test_p0_smoke.py p0, feature/<name>/ p1: announcement_popup, i18n, navigation, wallet)
tests/rc/conftest.py        — rc-specific overrides: site_config=rc, go_home (+ dismiss announcement popup)
tests/lt/                   — lt site tests (test_p0_smoke.py p0, test_locale_visual_matrix.py p2 [skipped], feature/<name>/ p1: auth, copy, i18n, member, public, visual, wallet)
tests/lt/conftest.py        — lt-specific overrides: site_config=lt, page fixture without MutationObserver
tests/re/                   — re site tests (test_p0_smoke.py p0, feature/<name>/ p1: announcement_popup, copy, game, home_sections, i18n, member, navigation, sidebar, visual, wallet)
tests/re/conftest.py        — re-specific overrides: site_config=re, go_home
tests/rd/                   — rd site tests (test_p0_smoke.py p0, feature/<name>/ p1: announcement_popup, i18n, navigation)
tests/rd/conftest.py        — rd-specific overrides: site_config=rd, go_home
tests/qw/                   — qw site tests (test_p0_smoke.py p0, feature/visual/ p2)
tests/qw/conftest.py        — qw-specific overrides: site_config=qw, go_home (+ dismiss popup-mask)
utils/locale_helper.py       — set_locale(): injects i18n_locale cookie for lt site
utils/dialog_helper.py       — helpers: dismiss server error popups, wait for loading animation
utils/screenshot_helper.py   — element-highlight screenshot system, auto README.md generation
screenshots/<site_id>/<timestamp>/<smoke|feature>/<test_name>/  — per-test screenshot folders, auto-categorized (in .gitignore)
screenshots/lt/vr_reference/                    — VR reference screenshots (no comparison, manual review only)
docs/                        — team-shared documentation (tracked in git)
dev-notes/                   — personal developer notes (gitignored except README.md)
```

**Environment detection** in `conftest.py`: detects WSL vs Windows vs Linux, auto-starts Windows Chrome over CDP if needed, injects a MutationObserver to auto-close server error popups.

**Fixtures** (conftest.py):
- `site_config` (session-scoped) — loads credentials for the selected site
- `page` (function-scoped) — fresh browser context per test, window maximized
- `logged_in_page` (function-scoped) — pre-authenticated page (RC smoke 使用；LT smoke 已改用 `page` 自行登入)
- `class_logged_in_page` (class-scoped) — logs in once per class; share session across functional tests
- `go_home` (function-scoped) — navigates back to home + clears popups before each functional test; use with `class_logged_in_page`
- `auto_screenshot` (autouse) — attaches `ScreenshotHelper` to page; auto-categorizes tests into `smoke/` or `feature/` subfolder; generates `screenshots/<site_id>/<timestamp>/<category>/<test_name>/README.md` after each test
- `auto_logout_after_test` (autouse) — logs out after each smoke test (`page` fixture only)

**Markers** (pytest.ini): `p0`, `p1`, `p2`, `login`, `home`, `member`, `wallet`, `i18n`, `language`, `copy`, `visual`, `visual_regression`, `locale_layout`, `docker_only`, `api`, `dashboard`, `game`, `flaky`, `lt`, `rc`, `re`, `rd`, `qw`

## Multi-site Factory Pattern

`pages/factory.py` 使用兩個 registry dict 路由 `site_id` → page class：
- `_LOGIN_PAGE_REGISTRY`：`site_id` → `(module_path, class_name)`
- `_HOME_PAGE_REGISTRY`：同上
- 外部只透過 `get_login_page_class(site_id)` / `get_home_page_class(site_id)` 存取
- **不使用 if/else fallback 到預設站台**；未註冊的 `site_id` 必須拋 `ValueError`，訊息包含可用站台列表
- 新增站點只需在兩個 registry 各加一行，不動 function 邏輯

測試檔**禁止**直接 `from pages.<site_id>.xxx import ...`，必須透過 factory 取得 class 以維持跨站復用彈性。

## Agent Skills

本 repo 有以下 user-invocable skills（位於 `.claude/skills/`），用於不同類型的工作：

| Skill | 用途 |
|-------|------|
| `ui-test-author` | 新增/修改 testcase、page object、fixture；含新增站點 onboarding checklist |
| `pom-architect` | 規劃/調整 Page Objects、component objects、multi-site UI 結構與跨站共用策略 |
| `test-review` | Review 測試變更，逐項檢查 flaky、脆弱 selector、multi-site 擴展性風險 |
| `git-commit` | 提交前檢查、整理 diff、建議驗證步驟與 commit message |
| `env-sync` | 維持 `.env` 與 `.env.example` 結構同步；處理同事發放的新 .env 範本合併 |
| `selector-probe` | 用 agent-browser CLI 即時 probe 網頁 selector / ARIA 結構，補強 chrome-devtools MCP 在「寫測試前探勘」與「pytest 失敗 root cause 分析」場景 |

各 skill 的指引與本 CLAUDE.md 互補：CLAUDE.md 是 repo 層級的 source of truth，skills 包含更詳細的 checklist 與實戰 pitfalls。Authoring 用 `ui-test-author`、設計 POM 用 `pom-architect`、review 用 `test-review`、commit 前用 `git-commit`、動 .env 用 `env-sync`、probe selector 用 `selector-probe`。

**完整接力工作流**（為什麼這 6 個 skill、如何接力、真實任務範例、避讓機制）見 [`docs/agent-skills-workflow.md`](docs/agent-skills-workflow.md)。

## Subagents

本 repo 還有 3 個 main agent 可主動派工的 subagent（位於 `.claude/agents/`，獨立 context 不污染主對話）：

| Subagent | 用途 | Inject 的 skill | 工具範圍 |
|---------|------|---------------|---------|
| `test-author` | 新增/修改 testcase、POM、實作功能驗證 | `ui-test-author`、`pom-architect` | Read/Write/Edit/Bash/Grep/Glob |
| `test-reviewer` | Read-only review、找 flaky / cover-up / 跨站風險 | `test-review` | Read/Grep/Glob/Bash |
| `selector-explorer` | DOM 探查、ARIA 拿 selector | `selector-probe` | Read/Grep/Glob/Bash |

Skill 是**人類**用 `/skill-name` 觸發；subagent 是 **main agent** 主動 delegate。詳細差異、三 agent 接力 SOP、避讓機制見 [`docs/agent-skills-workflow.md`](docs/agent-skills-workflow.md) 的 `## Subagent 層` 段。

**新站 onboarding 完整 SOP**（含 mermaid 流程圖、subagent / skill 觸發條件、QW 實作經驗的坑、預估時間）見 [`docs/new-site-onboarding-workflow.md`](docs/new-site-onboarding-workflow.md)。

## Documentation vs Developer Notes

This repo has **two distinct documentation folders** with different purposes and git-tracking policy. When creating or editing markdown files, pick the right folder and follow the convention.

### `docs/` — Team-shared, tracked in git

存放「**需要跨開發者共享、且相對穩定**」的文件。任何新加入的團隊成員應該能透過閱讀本資料夾建立對測試套件與產品的理解。

**應放入的內容**：
- 產品/技術**事實參考**（例如多語系文案對照、API 契約、測試資料定義）
- 測試策略與規格（測試方向、覆蓋原則、case 設計規範）
- 架構決策（page object 設計、fixture 分層、站台擴充方式）
- 慣例定義（命名規則、selector 策略、截圖規範）
- Onboarding 指南

**特徵**：不常變動、需要共識、跨開發者有效、新進成員必讀。

### `dev-notes/` — Personal, gitignored (except README.md)

存放「**個人的、經常變動的、不需團隊共識**」的工作筆記。文件僅代表撰寫者當下的觀察或想法，不是產品/測試的事實來源。

**應放入的內容**：
- 個人 TODO / 待辦清單、改善提案
- 探索筆記、實機發現、selector 嘗試紀錄
- Debug 紀錄、問題排查過程
- 效能實驗、benchmark 結果
- 想法草稿、未成熟的架構構想
- 測試覆蓋比對（與舊版/其他專案對照）

**特徵**：經常變動、個人觀點、可能未成熟、可丟棄。

**Git 設定**：`.gitignore` 設為 `dev-notes/*` 與 `!dev-notes/README.md`，只有 README 被追蹤。

### 判斷原則（when in doubt）

寫新文件前先問自己：

1. **「半年後任何人看到這份文件都能理解並受用嗎？」** → 是 `docs/` / 否 `dev-notes/`
2. **「這是產品/測試的事實，還是我目前的想法？」** → 事實 `docs/` / 想法 `dev-notes/`
3. **「新進成員需要讀這份文件才能上手嗎？」** → 需要 `docs/` / 不需要 `dev-notes/`

若某份 `dev-notes/` 的筆記後來成熟並獲得團隊共識，請**升級**移到 `docs/` 並調整內容為正式文件。反之，若 `docs/` 中某份文件變成僅個人觀點的 WIP 清單，應移到 `dev-notes/`。

## Visual Regression (lt / rc / qw)

LT、RC、QW 皆採用 **reference screenshot** 策略：存檔供人工確認，不做 pixel 比對（跨環境解析度不穩定）。

```bash
# VR reference 截圖（輸出至 screenshots/<site_id>/vr_reference/）
.venv/bin/pytest tests/lt/feature/visual/test_visual_regression.py -m visual_regression
.venv/bin/pytest tests/rc/feature/visual/test_visual_regression.py -m visual_regression
.venv/bin/pytest tests/qw/feature/visual/test_visual_regression.py -m visual_regression

# DOM 層視覺健康度（非截圖）
.venv/bin/pytest -m visual
```

**架構**：
- 共用邏輯（`save_vr_screenshot` / `screenshot_with_mask`）集中在 `utils/visual_helpers.py`
- 各站動態元素 selector 放在 `tests/<site_id>/feature/visual/helpers.py` 的 `BANNER_SELECTORS`
- `screenshots/<site_id>/vr_reference/` 為 gitignored（依 `screenshots/` 全站規則），僅本機存放供人工 review
- 新增站點要加 VR：複製 `tests/<site_id>/feature/visual/` 模板，調整 BANNER_SELECTORS 與 test 檔中傳入 `save_vr_screenshot` 的 `site_id` 參數即可

**swiper 相容性**：部分站點 `.swiper-wrapper` / `.swiper-slide` 也命中 `.swiper` selector 但沒掛 swiper instance；`screenshot_with_mask` 用 optional chaining（`autoplay?.stop?.()`、`slideTo?.(0, 0)`）保護，不可回退成直呼 method。

> `tests/lt/test_locale_visual_matrix.py`（WIN-LVIS）目前全部 `skip`。

## Screenshot System

Every test automatically gets a `ScreenshotHelper` via the `auto_screenshot` autouse fixture. In POM methods and test files, use `get_screenshotter(page)` to access it:

```python
from utils.screenshot_helper import get_screenshotter

sh = get_screenshotter(page)
if sh: sh.capture(locator, "label")       # highlight element with red box → screenshot
if sh: sh.full_page("label")              # full-page screenshot (no element highlight)
```

Label naming convention:
- `click_XXX` → 點擊
- `fill_XXX` → 填入
- `verify_XXX` → 驗證
- `loading_XXX` → Loading 狀態

After each test, `screenshots/<site_id>/<timestamp>/<smoke|feature>/<test_name>/README.md` is auto-generated in Traditional Chinese with step-by-step screenshots embedded. Category is auto-detected: tests under `feature/` → `feature`, others → `smoke`.

## Coding Conventions

### 元素互動
一般元素互動前先呼叫 `scroll_into_view_if_needed()` 再 click/fill/type。

```python
element.scroll_into_view_if_needed()
element.click()
```

### 已知互動例外（改用 `dispatch_event("click")`）

以下情境 `.click()`（含 `force=True`）會固定 timeout 或丟 "Element is outside of the viewport"，必須改用 `dispatch_event("click")` 直接觸發 DOM event：

| 情境 | Selector 範例 | 原因 |
|------|---------------|------|
| RC CSS-hidden sidebar | `.sidebar-item.*`（`width=0` 容器） | 永遠在 viewport 外 |
| LT member drawer 按鈕（如登出） | drawer 內按鈕 | 渲染位置在 viewport 外 |
| 常駐 overlay backdrop 攔截點擊 | 如 LT drawer closed 狀態 | Pointer events 被攔截 |

### 其他互動規則
- **DOM re-render 後不要對舊 locator 呼叫 `scroll_into_view_if_needed()`**（element 可能 detached）。改用 `page.evaluate("window.scrollBy(0, N)")`。
- **Sidebar hidden nodes 與 content 同文案**（RC 站 `p.text-black`）：用 `p:not(.text-black)` 排除，避免 `text=XXX` 命中 hidden node。
- 禁止裸 `time.sleep()`，優先使用 Playwright `expect` 與可判定事件等待。

### Selector 規則
- **多語系站台（LT）禁止綁死文案**：placeholder、button name、footer tab 文字會隨 locale 變化。使用 CSS-based selector（如 `input.input-style:not(.password-input)`、`input.password-input`、`button.base-btn.type1`）或結構化 locator（如 `.footer-bg .content` 取 `.last`/`.nth(0)`）。
- **`.first` / `.last` 是 property，不是 method**：寫成 `.first()` 會觸發 `__call__` 錯誤。
- Selector 優先順序：穩定屬性 > role/結構化 locator > 穩定文案 > nth-child/深 CSS 鏈。

### LT SPA Login：必須等 `networkidle`
LT 使用 React SPA。若 form 在 `networkidle` 前被填入，登入 API 會成功但 SPA 不會離開 `/login`。前往 `/login` 時必須使用 `wait_until="networkidle"`。

### Exception Handling
只在預期元素缺席或 timeout 時 catch `PlaywrightTimeoutError`（`from playwright.sync_api import TimeoutError as PlaywrightTimeoutError`）。禁止 `except Exception: pass` 靜默 playwright 操作錯誤。

## Git Commit Rules

- 任何 commit / push 動作需先經使用者確認。
- **禁止**在 commit message 加入 `Co-Authored-By: Claude ...` 或任何 Claude 署名。
