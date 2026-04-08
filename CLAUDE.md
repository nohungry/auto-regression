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
pages/factory.py             — routes site_id → correct LoginPage/HomePage class
pages/drc/                   — drc site Page Objects (LoginPage, HomePage)
pages/dlt/                   — dlt site Page Objects (LoginPage, HomePage)
tests/drc/                   — drc site tests (test_p0_smoke.py p0, feature/<name>/ p1)
tests/drc/conftest.py        — drc-specific overrides: site_config=drc, go_home (+ dismiss announcement popup)
tests/dlt/                   — dlt site tests (test_p0_smoke.py p0, test_functional.py p1/p2, test_locale_visual_matrix.py p2)
tests/dlt/conftest.py        — dlt-specific overrides: site_config=dlt, page fixture without MutationObserver
tests/dlt/__snapshots__/     — Visual Regression baseline PNGs (pytest-playwright-snapshot)
utils/locale_helper.py       — set_locale(): injects i18n_redirected_lt cookie for lt site
utils/dialog_helper.py       — helpers: dismiss server error popups, wait for loading animation
utils/screenshot_helper.py   — element-highlight screenshot system, auto README.md generation
screenshots/                 — per-test screenshot folders (auto-generated, in .gitignore)
screenshots/vr_reference/    — home_shell / member_menu archive screenshots (no comparison, for manual review)
```

**Environment detection** in `conftest.py`: detects WSL vs Windows vs Linux, auto-starts Windows Chrome over CDP if needed, injects a MutationObserver to auto-close server error popups.

**Fixtures** (conftest.py):
- `site_config` (session-scoped) — loads credentials for the selected site
- `page` (function-scoped) — fresh browser context per test, window maximized
- `logged_in_page` (function-scoped) — pre-authenticated page for smoke tests
- `class_logged_in_page` (class-scoped) — logs in once per class; share session across functional tests
- `go_home` (function-scoped) — navigates back to home + clears popups before each functional test; use with `class_logged_in_page`
- `auto_screenshot` (autouse) — attaches `ScreenshotHelper` to page; generates `screenshots/<test_name>/README.md` after each test
- `auto_logout_after_test` (autouse) — logs out after each smoke test (`page` fixture only)

**Markers** (pytest.ini): `p0`, `p1`, `p2`, `login`, `home`, `visual_regression`, `locale_visual`, `dlt`

## Visual Regression (dlt site)

Uses `pytest-playwright-snapshot` (not `expect(page).to_have_screenshot()` which is JS-only).

**Building / updating baselines:**
```bash
.venv/bin/pytest tests/dlt/test_functional.py -m visual_regression --update-snapshots
.venv/bin/pytest tests/dlt/test_locale_visual_matrix.py --update-snapshots
```

**Comparing against baselines:**
```bash
.venv/bin/pytest tests/dlt/test_functional.py -m visual_regression
.venv/bin/pytest tests/dlt/test_locale_visual_matrix.py
```

**Dynamic content masking** — `_screenshot_with_mask()` hides banner images, game thumbnails, and the announcement bar before screenshotting, then restores them. Also stops Swiper carousel autoplay and resets to slide 0 for consistency.

**home_shell and member_menu** — These tests contain live dynamic content (announcement ticker, hot games list) that changes too frequently for pixel-perfect comparison. They use `_save_screenshot()` instead: screenshots are saved to `screenshots/vr_reference/` for manual review but no assertion is made.

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

After each test, `screenshots/<test_name>/README.md` is auto-generated in Traditional Chinese with step-by-step screenshots embedded.

## Coding Conventions

### Element Interaction Rule
**Always call `scroll_into_view_if_needed()` before any element interaction** (`.click()`, `.fill()`, `.type()`, etc.) in both Page Objects (`pages/`) and test files (`tests/`).

```python
# Correct
element.scroll_into_view_if_needed()
element.click()

# Wrong
element.click()
```

**Exception — CSS-hidden sidebar items** (`.sidebar-item.*`): these elements live in a container with `width=0` and are permanently outside the viewport. `scroll_into_view_if_needed()` and `click(force=True)` both fail with "Element is outside of the viewport". Use `dispatch_event("click")` instead to fire the DOM event directly:

```python
# Correct for sidebar items
page.locator(".sidebar-item.user").dispatch_event("click")

# Wrong — will throw "Element is outside of the viewport"
sidebar.scroll_into_view_if_needed()
sidebar.click(force=True)
```

### Exception — DOM Re-render After Tab/Navigation Clicks

When a click triggers a DOM re-render (e.g., switching tabs that rebuild a grid), **do not call `scroll_into_view_if_needed()` on the target element** — the element reference may become detached. Use `page.evaluate("window.scrollBy(0, N)")` to scroll the window instead:

```python
# Wrong — element may be detached after tab re-render
grid.scroll_into_view_if_needed()

# Correct
page.evaluate("window.scrollBy(0, 400)")
```

### Exception — Sidebar Hidden Nodes Shadowing Content Nodes

The sidebar uses `p.text-black` for nav labels (hidden, `width=0` container). These same texts (e.g., "T9真人") also appear in the main content area. Using `locator("text=T9真人").first` will resolve to the hidden sidebar node. Exclude with `:not(.text-black)`:

```python
# Wrong — resolves to hidden sidebar p.text-black node
el = page.locator("text=T9真人").first

# Correct — targets visible content card
el = page.locator("p:not(.text-black)", has_text="T9真人").first
```

### Exception — lt 站 Drawer 按鈕（登出）Outside Viewport

The lt site's member drawer renders its buttons (登出) outside the viewport. `scroll_into_view_if_needed()` + `click()` will always fail with "Element is outside of the viewport". Use `dispatch_event("click")` instead:

```python
# Correct for lt drawer buttons (e.g., logout)
self.logout_btn.wait_for(state="visible", timeout=5000)
self.logout_btn.dispatch_event("click")

# Wrong — will throw "Element is outside of the viewport"
self.logout_btn.scroll_into_view_if_needed()
self.logout_btn.click()
```

### Exception — dlt 站 Login Form: Locale-agnostic Selectors

The dlt login form's placeholder text and button label change with locale. Always use CSS-based selectors instead of text-based ones:

```python
# Correct — works for all 5 locales (tw/cn/en/th/vn)
self.username_input = page.locator("input.input-style").nth(0)
self.password_input = page.locator("input.input-style").nth(1)
self.login_btn      = page.locator("button").first   # property, NOT method call

# Wrong — only works for tw locale
self.username_input = page.get_by_placeholder("請填寫4-10位的字母或數字")
self.login_btn      = page.get_by_role("button", name="登入")
```

Note: `.last` and `.first` in Python Playwright are **properties**, not methods. Do NOT call them as `.last()` or `.first()`.

### Exception — lt 站 SPA Login Form: Must Wait for networkidle

The lt site uses React (SPA). If form inputs are filled before the page reaches `networkidle`, the login succeeds at API level (cookie is set) but the SPA does **not** navigate away from `/login`. Always use `wait_until="networkidle"` when going to `/login`:

```python
# Correct
self.page.goto(self.login_url, wait_until="networkidle")

# Wrong — form may not be fully initialized; SPA won't redirect after submit
self.page.goto(self.login_url, wait_until="domcontentloaded")
```

### Exception Handling
Only catch `PlaywrightTimeoutError` (imported as `from playwright.sync_api import TimeoutError as PlaywrightTimeoutError`) when the intent is to handle an expected element absence/timeout. Never use bare `except Exception: pass` to silence playwright interactions.

## Git Commit Rules

- **Never** include `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` (or any Claude co-author line) in commit messages.

## Adding Tests / Sites

- New page objects go in `pages/`, following the existing POM pattern.
- New sites: add `SITE_XXX_URL`, `SITE_XXX_USERNAME`, `SITE_XXX_PASSWORD` to `.env`.
- New test markers must be declared in `pytest.ini` under `markers`.
