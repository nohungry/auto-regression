---
name: ui-test-author
description: 新增或修改 Python pytest-playwright 測試、Page Objects、與 multi-site UI 自動化案例。當使用者要新增測試案例、修改 page object、擴充新站點測試、處理 selector/interaction 問題、或討論 fixture 選用時，使用此 skill。
---

# Purpose
用於此 repo 的 UI 測試開發工作，包含：
- 新增 smoke / functional / visual regression 測試。
- 修改 `pages/` 下的 page objects。
- 在不破壞 multi-site 架構下擴充新舊站點測試。
- 讓測試案例、page objects、fixtures 維持可讀、可維護、可擴展。

# Repo context
- 技術棧：Python + pytest-playwright。
- 一律使用 `.venv/bin/pytest` 執行。
- **雙系統 multi-site 架構**：
  - 前台（玩家端）：`pages/factory.py` 依 `site_id` 路由到 `pages/<site_id>/`；UI 測試位於 `tests/<site_id>/`，結構為 `test_p0_smoke.py`（smoke）+ `feature/<feature_name>/`（功能驗證）。
  - 後台 dashboard（代理/管理端）：`pages/dashboard/factory.py`（**獨立 registry**）依 `site_id` 路由到 `pages/dashboard/<site_id>/`；UI 測試位於 `tests/dashboard/<site_id>/`。
  - API 層測試位於 `tests/api/<site_id>/`，以 `requests` 直打，**不啟動瀏覽器**、**不 import 任何 `pages/*`**。
  - 前台與後台為兩套獨立系統，**禁止互相 import**。已註冊站點以兩個 factory 的 registry 為準。
- 各站測試目錄下有自己的 `conftest.py`，負責覆寫 `site_config` 與站台特定 fixture。
- LT 站目前採 **reference screenshot** 策略：截圖輸出至 `screenshots/lt/vr_reference/` 供人工確認，不做 pixel 比對。`tests/lt/__snapshots__/` 為舊 baseline，無測試引用。

# Scope rules
1. 此 skill 負責 testcase authoring、page object 調整、與小幅測試重構。
2. 此 skill 不負責直接批准 snapshot 更新。
3. 此 skill 不負責直接 commit / push / merge。
4. 若變更涉及 `conftest.py`、`pages/factory.py`、跨站共用 fixture、snapshot 結構，需主動說明影響範圍。
5. 若需求已超出單一 testcase / page object 編修，應提醒改用 `pom-architect` 或 `test-review` 搭配處理。

# Authoring rules
1. 優先沿用既有 fixtures，例如 `page`、`logged_in_page`、`class_logged_in_page`、`go_home`。
2. Smoke 測試放在 `tests/<site_id>/test_p0_smoke.py`（p0 marker）；功能驗證依功能拆分到 `tests/<site_id>/feature/<feature_name>/`（如 `wallet/`、`i18n/`、`member/`）。API 層測試（不啟動瀏覽器）放 `tests/api/<site_id>/`。
3. 若是登入後功能測試，優先使用既有登入 fixture 與回首頁流程，避免每個 test 重複登入。
4. 不要在 test 中堆大量 locator；可重用互動應移到 page object 或 component object。
5. 不要隨意新增新的 fixture 名稱，除非現有 fixture 無法表達需求。
6. 新增站點時，沿用既有 `tests/<site_id>/`、`pages/<site_id>/`、factory routing 結構，不另創平行架構。

# Multi-site rules
1. site-specific 差異應優先實作在 `pages/<site_id>/` 內，而不是污染共用層。
2. 若多個站點共用同一 public 行為，可維持一致 method name，但允許各站內部分別實作。
3. 若新站點只在 selector 或局部互動不同，不應直接複製整套測試邏輯。
4. 若新站點具多語系、易變文案、特殊 layout 或 viewport 行為，應將其視為 site-specific constraint 並在實作中保留彈性。

# Adding a new site — checklist
新增站點時，依目標範圍完成對應分支。**前台是必須，後台與 API 視該站需求而定**。

## A. 前台（玩家端）— 一律必做

1. **.env**：新增 `SITE_<ID>_URL`、`SITE_<ID>_USERNAME`、`SITE_<ID>_PASSWORD`（同步更新 `.env.example`，密碼欄留空）。
2. **`pages/<site_id>/`**：建立站點目錄，至少包含 `__init__.py`、`login_page.py`、`home_page.py`。
   - `LoginPage` 必須實作 `goto_and_login(username, password)` 方法。
   - `HomePage` 必須實作 `verify_logged_in()`（輕量、無副作用）、`verify_login_success(username)`（完整 E2E，可含副作用）、`dismiss_any_popups()`、`is_logged_in()`、`logout()` 方法。LT 站另有 `verify_username_in_drawer(username)`（開 drawer + reload，副作用大，只在需要驗 username 文字時用）。
3. **`pages/factory.py`**：在 `_LOGIN_PAGE_REGISTRY` 與 `_HOME_PAGE_REGISTRY` dict 中各加一行，註冊新站的 import path。不可使用 fallback/default，未註冊的 site_id 必須拋出 `ValueError`。
4. **`tests/<site_id>/conftest.py`**：建立站台專用 conftest，至少覆寫 `site_config` fixture（hardcode 該站 site_id）。
5. **評估是否需覆寫 `page` fixture**：全域 `conftest.py` 的 `_new_configured_page()` 會注入 `toast-confirm-btn` MutationObserver（rc 站特有的伺服器錯誤彈窗處理）。若新站不需要此行為，必須在 `tests/<site_id>/conftest.py` 覆寫 `page` fixture，移除注入邏輯。同理評估 `class_logged_in_page` 是否也需覆寫。
6. **`pytest.ini`**：若有新 marker，在 `markers` 區塊中宣告。
7. **`tests/<site_id>/`**：建立 `__init__.py`、`test_p0_smoke.py`。
8. **文檔同步（必做，依 `CLAUDE.md` 文檔維護對照表）**：新站**務必**同步 root `README.md`（站台表 / 目錄樹 / 執行指令 / markers 表）與 `CLAUDE.md`（Architecture 樹 / 站點清單 / factory 段）；新增 marker 另同步 README markers 表 + CLAUDE.md Markers + `pytest.ini`。⚠️ 漏改 README 會被 docs-sync hook 直接 block（新前台站點、marker 變動皆有 deterministic 硬規則）。

## B. 後台 dashboard（代理/管理端）— 該站若有後台需測就做

1. **.env**：新增後台環境變數組（同步更新 `.env.example`）：
   - `SITE_<ID>_DASHBOARD_URL`（必要）
   - `SITE_<ID>_DASHBOARD_USER`、`SITE_<ID>_DASHBOARD_PASS`（總代帳號）
   - `SITE_<ID>_DASHBOARD_TOTP`（若該站後台啟用 2FA）
   - `SITE_<ID>_DASHBOARD_AGENT_USER`、`SITE_<ID>_DASHBOARD_AGENT_PASS`（自動化代理帳號，限定權限）
2. **`pages/dashboard/<site_id>/`**：建立後台站點目錄，至少包含 `__init__.py`、`login_page.py`、`management_page.py`。
   - `DashboardLoginPage` 必須實作後台登入流程（含 TOTP 若有）。
   - `ManagementPage` 提供後台主要操作入口（帳號管理、報表、佣金等）。
3. **`pages/dashboard/factory.py`**：在 `_DASHBOARD_LOGIN_REGISTRY` 與 `_DASHBOARD_MANAGEMENT_REGISTRY` 兩個 dict 中**各加一行**。**任一缺漏會在 runtime 才報錯**。
4. **`tests/dashboard/<site_id>/conftest.py`**：建立後台專用 conftest，覆寫 `site_config` 與後台特有 fixture（如 TOTP secret 載入、agent vs admin 登入策略切換）。

   **目前已有站點的後台 conftest 慣例**（非硬規定，新站可依需求偏離但需在 docstring 註明理由）：
   - 登入採 **session-scoped** fixture（後台登入成本高，含 TOTP / 多步驟對話框，session 級登入大幅省時）。
   - 用 `browser.new_context()` 自建獨立 context，**不繼承根 `conftest.py` 的 `page` fixture**（避開前台專屬的 toast MutationObserver 注入）。
   - 若新站需 per-test 狀態隔離（如不可重入的測試），可改 function-scope，但需在 conftest docstring 標示原因。

5. **`tests/dashboard/<site_id>/`**：建立 `__init__.py`、`test_p0_smoke.py`。
6. 後台與前台為獨立系統，**禁止互相 import**（詳細規則見下方 `Factory rules > 跨系統規則`）。

## C. API 層 — 該站若有 API 測試需求就做

1. **.env**：新增 `SITE_<ID>_API_URL`、`SITE_<ID>_API_DOMAIN`、`SITE_<ID>_COMPANYCODE`（同步更新 `.env.example`）。companycode 為公開 site code，非機密，可保留真實值；值不一定等於 site_id（例如 site_id=`rc` 但 companycode=`drc`、site_id=`lt` 但 companycode=`dlt`）。
2. **`tests/api/<site_id>/conftest.py`**：建立 API 專用 conftest，提供 `site_config`、`api_base_url`、`api_headers` fixture。
3. **`tests/api/<site_id>/`**：建立 `__init__.py` 與 test 檔（`test_auth.py`、`test_wallet.py` 等）。
4. **不啟動瀏覽器** — API 測試只用 `requests` 直打。跨系統 import 規則見下方 `Factory rules > 跨系統規則`。

## D. 驗證

- 前台：`.venv/bin/pytest tests/<site_id>/ -v`
- 後台：`.venv/bin/pytest tests/dashboard/<site_id>/ -v`
- API：`.venv/bin/pytest tests/api/<site_id>/ -v`
- 確認 factory 抛 `ValueError` 機制正常（未註冊 site_id 應明確報錯）。

# Factory rules
本 repo 有**兩套獨立 factory**，前台與後台各自一套，互不互通：

## 前台 — `pages/factory.py`
1. 使用兩個 registry dict：`_LOGIN_PAGE_REGISTRY` 與 `_HOME_PAGE_REGISTRY`，各自映射 `site_id` → `(module_path, class_name)`。
2. 禁止使用 if/else fallback 到預設站台；未註冊的 `site_id` 必須拋出明確 `ValueError`，訊息包含可用站台列表。
3. 新增站點只需在兩個 registry 中各加一行，不需修改 function 邏輯。
4. factory 只負責回傳 class，不負責 instantiate。
5. 外部呼叫者一律使用 `get_login_page_class(site_id)` / `get_home_page_class(site_id)`，不直接存取 registry dict。

## 後台 — `pages/dashboard/factory.py`
1. 使用兩個 registry dict：`_DASHBOARD_LOGIN_REGISTRY` 與 `_DASHBOARD_MANAGEMENT_REGISTRY`。
2. 規則與前台 factory 相同（無 fallback、外部走 getter function）。
3. 新增後台站點需在兩個 registry **都**註冊；任一缺漏會在 runtime 才報錯。
4. 後台 factory 與前台 factory 為獨立模組，不互相 import。

## 跨系統規則
1. 前台檔案（`pages/<site_id>/*`、`tests/<site_id>/*`、根 `conftest.py`）**禁止** import `pages.dashboard.*`。
2. 後台檔案（`pages/dashboard/<site_id>/*`、`tests/dashboard/<site_id>/*`）**禁止** import 前台 `pages.<site_id>.*`。
3. API 測試（`tests/api/<site_id>/*`）**禁止** import 任何 `pages/*`；只用 `requests` 直打。

# Site-specific conftest pattern
每個站點的 `tests/<site_id>/conftest.py` 負責：
- **必要**：覆寫 `site_config` fixture，hardcode 該站 site_id，讓 `pytest tests/<site_id>/` 不需帶 `--site` 參數。
- **視需要**：覆寫 `page` fixture（例如移除 MutationObserver 注入）。
- **視需要**：覆寫 `class_logged_in_page` fixture（若全域版本的行為不適合該站）。
- **視需要**：新增站台專用 fixture（例如特殊的 locale 設定）。

# POM rules
1. test 檔只描述 scenario、assertion 與測試意圖，不直接堆疊 DOM 細節。
2. 可重用互動封裝進 page object；跨頁重複區塊封裝成 component object。
3. 若差異只存在於單一站台，實作應留在該站台目錄，不要過早抽象成共用 base class。
4. Page object 方法名稱應描述使用者行為或頁面意圖，例如 `login_as()`、`open_wallet_tab()`、`close_server_error_dialog()`。
5. 不要把整段商業流程硬塞在一個超長 page object method；複合流程應由 test 組合多個可讀性高的方法。
6. test 檔應透過對應 factory 取得 page class（或透過 fixture 間接取得）：前台走 `pages/factory.py`、後台走 `pages/dashboard/factory.py`。不應直接 `from pages.<site_id>.xxx import` 或 `from pages.dashboard.<site_id>.xxx import`，以維持跨站復用彈性。

# Interaction rules
1. 一般元素互動前，先呼叫 `scroll_into_view_if_needed()` 再 click/fill/type。
2. 若元素屬於已知 viewport 例外（如 CSS hidden sidebar、drawer 內按鈕），應使用 `dispatch_event("click")`。
3. 若 overlay 元素（如 fixed drawer backdrop）常駐 DOM 且在「關閉」狀態下仍攔截 pointer events，一般 `.click()` 會永遠 timeout，必須用 `dispatch_event("click")`。確認方式：DevTools 觀察點擊是否被 overlay 攔截。
4. 若點擊後會引發 DOM re-render，不要對舊 locator 呼叫 scroll；改用 `page.evaluate("window.scrollBy(0, N)")` 等頁面層級處理方式。
5. 禁止使用裸 `time.sleep()` 或不必要的 hard wait。
6. 優先使用 Playwright expect 與可判定事件等待，不依賴脆弱 timing。

# Selector rules
1. 優先使用既有穩定 selector 模式，避免脆弱文字 selector。
2. 多語系或文案易變站點，必須使用 locale-agnostic selector，不可綁死 placeholder / button text。
3. 若 hidden node 與 visible node 可能同文案，應避開 hidden node，改用更精準 locator。
4. Python Playwright 的 `.first` / `.last` 是 property，不可寫成 `.first()` / `.last()`。
5. selector 優先順序：穩定屬性 > role / 結構化 locator > 穩定文案；避免 nth-child 與過深 CSS 鏈。

# Screenshot system rules
本 repo 使用 `ScreenshotHelper` 自動截圖系統，POM 方法與測試中應遵守：

1. 透過 `from utils.screenshot_helper import get_screenshotter` 取得當前 page 的 helper。
2. 使用前務必檢查 `sh = get_screenshotter(page); if sh:` — helper 可能不存在。
3. 元素截圖：`sh.capture(locator, "label")` — 會在元素上畫紅色 highlight 框再截圖。
4. **`sh.capture()` 前必須先 `locator.scroll_into_view_if_needed()`**，除非 locator 明確屬於 fixed / sticky 元素（如 navbar、右下浮動按鈕、bottom tabbar）。原因：`ScreenshotHelper` 用 `bounding_box()` 取元素座標畫紅框，若元素在 viewport 外，紅框會畫在 viewport 之外而頁面只截 viewport 範圍，結果是「斷言有過但截圖上看不到紅圈」，review 時會誤以為測試沒真正驗到。此規則同樣適用於 POM 方法內的 `sh.capture()`。
5. 全頁截圖：`sh.full_page("label")` — 無元素 highlight。
6. Label 命名規則：
   - `click_XXX`：點擊動作前截圖
   - `fill_XXX`：填入動作前截圖
   - `verify_XXX`：驗證結果截圖
   - `loading_XXX`：loading 狀態截圖
7. 每個測試結束後，`auto_screenshot` fixture 自動呼叫 `sh.generate_report()` 產生 `screenshots/<site_id>/<timestamp>/<test_name>/README.md`。
8. 在新增 page object method 時，應在關鍵操作點加入 `sh.capture()` / `sh.full_page()`，讓截圖報告能自動呈現完整操作流程。
9. **每個 test 的每個可判定步驟（interaction / navigation / assertion）都必須輸出截圖**，無截圖的測試視為不合格。即使是純 DOM metric 驗證（如 `page.evaluate()` 取得 scrollWidth / getBoundingClientRect），也必須在關鍵檢查點呼叫 `sh.full_page()` 或針對關鍵元素 `sh.capture()`，否則 reviewer 看不到 README.md 只能靠 code 猜測測試做了什麼。建議：
   - 純數值驗證（overflow / broken images / text clipping）：assertion **之前**呼叫 `sh.full_page("verify_XXX檢測_{metric}")`，label 中性（不承諾 pass/fail）。
   - 元素座標/對齊驗證（form alignment / viewport bounds）：對每個被量測的元素呼叫 `sh.capture()`（需 scroll_into_view），最後再補一張 `sh.full_page()` 呈現整體版面 — **全都要在 assertion 之前**。
   - 互動型驗證：每個 click / fill 前後都各一張（遵循 rule 6 的 label 命名）。

9a. **截圖必須在 `assert` / `expect(...)` / 可能拋例外的 helper 呼叫「之前」** — 否則失敗路徑（AssertionError / PlaywrightError / xfail）會讓後面那行截圖永遠跳過，資料夾空白，reviewer 沒有任何證據判斷失敗原因。這是常見反模式且**違反 rule 9 的「不合格」定義**。
   - ❌ **錯誤**：
     ```python
     assert broken == [], f"發現破圖：{broken}"
     if sh: sh.full_page(f"verify_首頁圖片無破圖_total{total}")   # fail 時永遠不會跑
     ```
   - ✅ **正確**：
     ```python
     if sh: sh.full_page(f"verify_首頁破圖檢測_total{total}_broken{len(broken)}")  # 先截圖
     assert broken == [], f"發現破圖：{broken}"
     ```
   - 對於 xfail(strict=True) 的守門 test 這條**尤其關鍵**：xfail 本質上每次都會 fail，截圖寫在 assert 後 = 永遠拿不到證據。
   - 對於呼叫可能失敗的 helper（`open_member_menu()`、`expect(...).to_be_visible()` 等），在**呼叫前**先存一張 `verify_XXX_pre_action` 作 snapshot 證據；helper 成功後再補一張 post-action。
   - Label 採**中性描述**（帶數值/狀態），不要承諾結果：
     - ❌ `verify_首頁無破圖` / `verify_登入成功` → 預設 pass 才寫出
     - ✅ `verify_首頁破圖檢測_found{n}` / `verify_登入完成_pre_navigation` → pass/fail 都合理
   - 規則源頭：`memory/feedback_screenshots_required_every_step.md`；歷史發現與範圍見 `dev-notes/screenshot-convention-followup.md`。
10. **動態值欄位（balance / username / 訂單號 / 時間戳等會隨時間或帳號變動的值）若只驗「非空」或「格式正確」而非「等於某值」，必須在下列兩處明確說明斷言策略，避免 reviewer 誤以為是寫死比對**：
    - **test docstring**：明確寫出「只驗非空 / 不寫死特定數值 / 截圖 label 帶值僅供 review」的斷言策略。
    - **screenshot label**：label 帶「**非空**」「**格式**」等關鍵字（例如 `verify_navbar信用額度非空_{balance_text}`），而不是 `verify_navbar餘額_{balance_text}`。原因：README.md 由 label 組出步驟文字，若 label 只帶值沒帶策略，review 時會誤認為值本身是斷言比對的 expected，檢查起來會懷疑測試是否太脆弱。此規則同樣適用於任何其他動態欄位（帳號切換、多站變動的 user profile、日期時間等）。

# Visual regression rules
1. `visual_regression` 只用於適合 baseline 比對的穩定畫面。
2. 動態內容頁面只存 reference screenshot，不做 snapshot assertion。
3. 更新 snapshot 前，先確認是產品預期變更，不可為了讓測試通過而直接更新 baseline。
4. 若新增或更新 snapshot，必須在輸出中明確說明原因與受影響檔案。

# Execution discipline
測試執行紀律 — subagent / 人工執行皆適用。

1. **單 session 防呆**：同一個測試帳號不可同時跑兩個 pytest process（含 API 測試與 UI 測試共用同帳號的情況）。後端以 token 機制互踢，會導致雙方 session 同時失效，後跑的測試看到不可預期狀態。執行前確認該帳號未被其他 process 使用；若不確定，先回報而不是直接跑。

2. **Regression notify before fix**：若原本通過的 test 突然 fail，**先停手回報主對話**，不要自己改 test 碼。原因：fail 經常代表產品 regression（後端壞掉、產品 bug、資料配置壞掉）而非測試 bug；自行修測試會把產品 regression 掩蓋掉，反而違背測試套件的存在價值。判斷流程：
   - 看截圖逐步確認 selector 命中、按鈕被按到、API 真的有送出
   - 若流程都正確但結果非預期（畫面「連線失敗」、API 錯誤碼、應有資料找不到）→ **真實 FAIL，回報主對話確認屬於測試問題還是 product regression**
   - 只有當問題明確屬於測試自身（selector 過時、timing race、test data 失效）才修測試碼
   - 不可加 `@pytest.mark.skip` 掩蓋未確認的 fail
   - 即使是 xfail(strict=True) 守門 test 突然 XPASS 也屬於需要回報的情況（產品狀態變動）

# State-mutating 測試設計（dashboard 尤其）
若測試會改動後端真實狀態（存入提取、額度調整、會員建檔、訂單操作），必須有可逆設計：

1. **設計可逆操作**：normal path 對稱還原 — 例如存 100 → 領 100 回到初始，整個 test 結束後狀態與起始相同。
2. **try/finally 補償**：中途失敗時反向動作不留髒資料。例如「存入成功但驗證失敗」必須 finally 補一次提取。
3. **連跑兩次也 idempotent**：不累積殘留、不踩到上次未清資料。Teardown 失敗的情境下也應該能再跑。
4. **docstring 註明 rollback 策略**：讓 reviewer 與下次維護者快速判斷補償邏輯是否完整。

具體實作 pattern 不限定（對稱還原 + try/finally、fixture teardown 補償、teardown diff 餘額補償都可），重點是「測試結束後狀態可預測」。Review 時 test-reviewer / `test-review` skill 會檢查相同維度。

# Output expectations
完成任務時，應：
- 說明修改了哪些 tests/pages/utils。
- 說明選擇 fixture、page object 與檔案位置的原因。
- 若有 multi-site 架構取捨，說明為何放在 site-specific 層或共用層。
- 若涉及 conftest 覆寫或 factory 變更，明確說明影響範圍。
- 列出建議執行的 pytest 指令。
- **完成 code 後，依 `CLAUDE.md` 的「文檔維護對照表」逐項更新對應 docs**：新站同步 root `README.md` + `CLAUDE.md`；新 marker 同步兩處 + `pytest.ini`；新 fixture/util 同步 CLAUDE.md 對應段。明確列出本次動了哪些 doc（或為何不需動）。
