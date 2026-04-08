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
- `DEFAULT_SITE` — which site config to use (e.g. `drc`)
- `CDP_URL` — Chrome remote debug URL (WSL/Linux only; e.g. `http://<WINDOWS_IP>:9223`)
- `SITE_<NAME>_URL/USERNAME/PASSWORD` — per-site credentials

## Running Tests

**Always use the project's virtualenv** located at `.venv/`:

```bash
.venv/bin/pytest                                                        # all tests
.venv/bin/pytest tests/drc/                                             # drc site only (no --site needed)
.venv/bin/pytest tests/dlt/                                             # dlt site only (no --site needed)
.venv/bin/pytest tests/dlt/test_p0_smoke.py -m p0                         # dlt p0 smoke tests
.venv/bin/pytest -m p0                                                  # by marker
.venv/bin/pytest -m login                                               # by marker
.venv/bin/pytest tests/drc/test_p0_smoke.py::TestLogin::test_login_success # single test
```

Reports are written to `reports/report.html` (self-contained HTML).

## Test Strategy

| 測試類型 | Fixture | Scope | 適用情境 |
|---------|---------|-------|---------|
| Smoke | `page` / `logged_in_page` | function | 每次測試獨立 context，測試後自動登出。驗證核心流程（登入/登出）。 |
| Functional | `class_logged_in_page` + `go_home` | class | 一個 class 只登入一次，測試間共用 session，`go_home` 每個測試前回首頁。適合功能驗證。 |

各站點測試放在 `tests/<site_id>/` 下；smoke 測試統一命名 `test_p0_smoke.py`，功能型測試放 `tests/<site_id>/feature/<feature_name>/`。

## Architecture

```
conftest.py                  — browser setup, environment detection (Windows/WSL/Linux), global fixtures
config/settings.py           — multi-site SiteConfig dataclass loaded from .env
pages/factory.py             — routes site_id → LoginPage/HomePage class via registry dict (no if/else fallback; unknown site_id raises ValueError)
pages/drc/                   — drc site Page Objects (LoginPage, HomePage)
pages/dlt/                   — dlt site Page Objects (LoginPage, HomePage)
tests/api/dlt/               — dlt site API-layer tests (no browser)
tests/drc/                   — drc site tests (test_p0_smoke.py p0, feature/<name>/ p1: announcement_popup, i18n, navigation, wallet)
tests/drc/conftest.py        — drc-specific overrides: site_config=drc, go_home (+ dismiss announcement popup)
tests/dlt/                   — dlt site tests (test_p0_smoke.py p0, test_locale_visual_matrix.py p2 [skipped], feature/<name>/ p1: auth, copy, i18n, member, public, visual, wallet)
tests/dlt/conftest.py        — dlt-specific overrides: site_config=dlt, page fixture without MutationObserver
tests/dlt/__snapshots__/     — Visual Regression baseline PNGs (legacy, currently unused)
utils/locale_helper.py       — set_locale(): injects i18n_redirected_lt cookie for lt site
utils/dialog_helper.py       — helpers: dismiss server error popups, wait for loading animation
utils/screenshot_helper.py   — element-highlight screenshot system, auto README.md generation
screenshots/<site_id>/<timestamp>/<test_name>/  — per-test screenshot folders (auto-generated, in .gitignore)
screenshots/dlt/vr_reference/                    — VR reference screenshots (no comparison, manual review only)
docs/                        — team-shared documentation (tracked in git)
dev-notes/                   — personal developer notes (gitignored except README.md)
```

**Environment detection** in `conftest.py`: detects WSL vs Windows vs Linux, auto-starts Windows Chrome over CDP if needed, injects a MutationObserver to auto-close server error popups.

**Fixtures** (conftest.py):
- `site_config` (session-scoped) — loads credentials for the selected site
- `page` (function-scoped) — fresh browser context per test, window maximized
- `logged_in_page` (function-scoped) — pre-authenticated page for smoke tests
- `class_logged_in_page` (class-scoped) — logs in once per class; share session across functional tests
- `go_home` (function-scoped) — navigates back to home + clears popups before each functional test; use with `class_logged_in_page`
- `auto_screenshot` (autouse) — attaches `ScreenshotHelper` to page; generates `screenshots/<site_id>/<timestamp>/<test_name>/README.md` after each test
- `auto_logout_after_test` (autouse) — logs out after each smoke test (`page` fixture only)

**Markers** (pytest.ini): `p0`, `p1`, `p2`, `login`, `home`, `member`, `wallet`, `i18n`, `language`, `copy`, `visual`, `visual_regression`, `locale_visual`, `api`, `dlt`

## Multi-site Factory Pattern

`pages/factory.py` 使用兩個 registry dict 路由 `site_id` → page class：
- `_LOGIN_PAGE_REGISTRY`：`site_id` → `(module_path, class_name)`
- `_HOME_PAGE_REGISTRY`：同上
- 外部只透過 `get_login_page_class(site_id)` / `get_home_page_class(site_id)` 存取
- **不使用 if/else fallback 到預設站台**；未註冊的 `site_id` 必須拋 `ValueError`，訊息包含可用站台列表
- 新增站點只需在兩個 registry 各加一行，不動 function 邏輯

測試檔**禁止**直接 `from pages.<site_id>.xxx import ...`，必須透過 factory 取得 class 以維持跨站復用彈性。

## Agent Skills

本 repo 有兩個 user-invocable skills（位於 `.claude/skills/`），用於不同類型的工作：

| Skill | 用途 |
|-------|------|
| `ui-test-author` | 新增/修改 testcase、page object、fixture；含新增站點 onboarding checklist |
| `test-review` | Review 測試變更，逐項檢查 flaky、脆弱 selector、multi-site 擴展性風險 |

兩個 skill 的指引與本 CLAUDE.md 互補：CLAUDE.md 是 repo 層級的 source of truth，skills 包含更詳細的 checklist 與實戰 pitfalls。Authoring 工作優先參考 `ui-test-author`，review 工作優先參考 `test-review`。

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

## Visual Regression (dlt site)

DLT 目前採用 **reference screenshot** 策略：存檔供人工確認，不做 pixel 比對（跨環境無法穩定）。

```bash
# VR reference 截圖（輸出至 screenshots/dlt/vr_reference/）
.venv/bin/pytest tests/dlt/feature/visual/test_visual_regression.py -m visual_regression

# DOM 層視覺健康度（非截圖）
.venv/bin/pytest tests/dlt/feature/visual/test_visual.py -m visual
```

> `tests/dlt/test_locale_visual_matrix.py`（WIN-LVIS）目前全部 `skip`；`tests/dlt/__snapshots__/` 為舊版 baseline 暫留，目前無測試引用。

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

After each test, `screenshots/<site_id>/<timestamp>/<test_name>/README.md` is auto-generated in Traditional Chinese with step-by-step screenshots embedded.

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
| DRC CSS-hidden sidebar | `.sidebar-item.*`（`width=0` 容器） | 永遠在 viewport 外 |
| DLT member drawer 按鈕（如登出） | drawer 內按鈕 | 渲染位置在 viewport 外 |
| 常駐 overlay backdrop 攔截點擊 | 如 DLT drawer closed 狀態 | Pointer events 被攔截 |

### 其他互動規則
- **DOM re-render 後不要對舊 locator 呼叫 `scroll_into_view_if_needed()`**（element 可能 detached）。改用 `page.evaluate("window.scrollBy(0, N)")`。
- **Sidebar hidden nodes 與 content 同文案**（DRC 站 `p.text-black`）：用 `p:not(.text-black)` 排除，避免 `text=XXX` 命中 hidden node。
- 禁止裸 `time.sleep()`，優先使用 Playwright `expect` 與可判定事件等待。

### Selector 規則
- **多語系站台（DLT）禁止綁死文案**：placeholder、button name 會隨 locale 變化。使用 CSS-based selector（如 `input.input-style`、`button.primary-btn`）或結構化 locator。
- **`.first` / `.last` 是 property，不是 method**：寫成 `.first()` 會觸發 `__call__` 錯誤。
- Selector 優先順序：穩定屬性 > role/結構化 locator > 穩定文案 > nth-child/深 CSS 鏈。

### DLT SPA Login：必須等 `networkidle`
DLT 使用 React SPA。若 form 在 `networkidle` 前被填入，登入 API 會成功但 SPA 不會離開 `/login`。前往 `/login` 時必須使用 `wait_until="networkidle"`。

### Exception Handling
只在預期元素缺席或 timeout 時 catch `PlaywrightTimeoutError`（`from playwright.sync_api import TimeoutError as PlaywrightTimeoutError`）。禁止 `except Exception: pass` 靜默 playwright 操作錯誤。

## Git Commit Rules

- 任何 commit / push 動作需先經使用者確認。
- **禁止**在 commit message 加入 `Co-Authored-By: Claude ...` 或任何 Claude 署名。
