---
name: pom-architect
description: 為 auto-regression repo 規劃或調整 Page Objects、component objects、與 multi-site UI 結構。當使用者要設計新站點的 POM 結構、重構既有 page object、討論 component 抽象策略、或評估跨站共用方案時，使用此 skill。
---

# Purpose
用於此 repo 的 Page Object Model（POM）設計與重構工作，包含：
- 規劃新站點、新頁面或新功能的 page object 結構。
- 調整既有 page object、component object、共用互動封裝方式。
- 保持 multi-site 架構下的可維護性，避免過度抽象。
- 協助測試邏輯與頁面互動職責分離，讓後續新增站點成本可控。

# Repo context
- 技術棧：Python + pytest-playwright。
- 專案採 multi-site 架構，站台差異透過 `pages/factory.py` 的 registry dict 與 `site_id` 路由處理。
- 各站 page objects 位於 `pages/<site_id>/`，已註冊站點以 `pages/factory.py` 的 registry 為準（前台），`pages/dashboard/factory.py` 的 registry 為準（後台）。前台與後台為兩套獨立 factory，不互相 import。
- 各站測試位於 `tests/<site_id>/`（前台）或 `tests/dashboard/<site_id>/`（後台），每站有自己的 `conftest.py` 覆寫 `site_config` 與站台特定 fixture。
- 截圖系統透過 `utils/screenshot_helper.py` 的 `get_screenshotter(page)` 運作，POM 方法中需在關鍵操作點加入截圖呼叫。
- 站點數量會持續增加，結構必須偏向可擴展，新增站點應只動 factory registry，而不需改 function 邏輯或共用層。

# Current POM structure
前台 page objects（由 `pages/factory.py` 路由）：

```
pages/
├── factory.py              — 前台 registry dict 路由 site_id → LoginPage/HomePage class
├── <site_id>/              — 各前台站台，每站含 login_page.py 與 home_page.py（站台差異見下方範例表）
└── dashboard/
    ├── factory.py          — 後台 registry dict 路由 site_id → DashboardLoginPage/ManagementPage class
    └── <site_id>/          — 各後台站台，每站含 login_page.py 與 management_page.py
```

站台清單以兩個 factory 的 registry dict 為準，不在此文件中列舉，避免文件與 registry 失同步。

# Page object public API contract
各站的 `LoginPage` 與 `HomePage` 雖然內部實作不同，但必須維持一致的 public API，供 `conftest.py` fixtures 與 test 檔呼叫：

**LoginPage 必要方法：**
- `__init__(self, page, base_url)` — 接收 Playwright page 與站台 URL
- `goto_and_login(username, password)` — 完整登入流程（goto → 開表單 → 填寫 → 送出）

**HomePage 必要方法：**
- `__init__(self, page)` — 接收 Playwright page
- `verify_logged_in()` — **輕量**驗證：已登入狀態（例如 hamburger / avatar 可見），**無副作用**。fixture 與多數測試優先用此方法。
- `verify_login_success(username)` — **完整 E2E** 驗證：登入成功且 username 文字可見，可含站點副作用（如 LT 會開 drawer + reload）。僅 `test_login_success` 這類 E2E 登入 TC 使用。
- `dismiss_any_popups()` — 清除進站彈窗（不適用的站點可實作為空方法）
- `is_logged_in()` → `bool` — 判斷目前是否已登入
- `logout()` — 完整登出流程

**HomePage 選配方法**（站點副作用重時使用）：
- `verify_username_in_drawer(username)` — LT 站專用：開 drawer 驗 username 文字後以 reload 關閉 drawer。`verify_login_success` 在 LT 等同於 `verify_logged_in` + `verify_username_in_drawer` 的 wrapper。

這些方法被 `conftest.py` 的 `logged_in_page`、`class_logged_in_page`、`auto_logout_after_test` 等 fixture 直接呼叫，變更簽名會破壞所有站點的測試基礎設施。`conftest` fixture 使用 `verify_logged_in()`（輕量）確保可跨站共用而不被站點副作用汙染。

# Design goals
1. 讓 test 保持 scenario 導向、可讀性高。
2. 讓 page object 專注封裝穩定互動與可重用 locator。
3. 讓 component object 承接跨頁重複區塊，而不是把所有邏輯塞進 base class。
4. 讓新增站點或調整站台差異時，不會破壞既有 routing 與共用 API。
5. 讓站點擴充時可以沿用相同模式，而不是每加一站就重新發明目錄結構。

# Architecture rules
1. test 檔負責 scenario 與 assertion，不負責管理大量 locator。
2. page object 代表一個頁面或主要頁面區塊；component object 代表跨頁重複元件，例如 header、sidebar、dialog、drawer。
3. 若元件只在單一站台存在，先保留在該站台目錄，不要提早搬到共用層。
4. 共用抽象必須來自實際重複與穩定模式，不可因為預測未來需求而先建立抽象基底。
5. `pages/factory.py` 使用 registry dict 映射 `site_id` → page class。新增站點只需加 registry 條目，不需改動 function 邏輯。未註冊的 site_id 拋出 `ValueError`。
6. 新增站點時，優先複用既有 public API 設計，而不是建立一套完全不同的方法命名風格。

# Factory integration
1. 新增 page type（如 `WalletPage`）時，需在 `factory.py` 新增對應 registry dict 與 getter function（如 `_WALLET_PAGE_REGISTRY`、`get_wallet_page_class()`）。
2. 若新 page type 只有部分站台需要，registry 只註冊需要的站台即可，但 getter function 的錯誤訊息必須清楚。
3. test 與 fixture 應透過 factory 取得 page class，不應直接 `from pages.<site_id>.xxx import`。
4. 外部呼叫者一律使用公開 getter function（如 `get_login_page_class()`），不直接存取 `_LOGIN_PAGE_REGISTRY` 等內部 dict；registry dict 為實作細節，隨時可能調整結構。

# Screenshot integration
POM 方法中應整合截圖系統：
1. 在方法開頭取得 `sh = get_screenshotter(self.page)`。
2. 關鍵操作前呼叫 `if sh: sh.capture(locator, "label")`。
3. 頁面狀態轉換後呼叫 `if sh: sh.full_page("label")`。
4. Label 命名規則：`click_XXX`、`fill_XXX`、`verify_XXX`、`loading_XXX`。
5. 截圖呼叫不影響功能邏輯，只是輔助產出操作流程報告。

# Design heuristics
1. 若同一互動在 2 個以上測試重複出現，評估搬入 page object。
2. 若同一 UI 區塊在多頁面或多站點出現，評估抽成 component object。
3. 若同名方法在不同站台語意相同但實作不同，可保留相同 public method name，分站內部分別實作。
4. 若流程很長，應拆成多個可組合方法，而不是建立一個包山包海的 mega-method。
5. 若抽共用層後充滿 site-specific if/else，表示抽象層級可能錯了。
6. 若新站點只有 selector 差異，優先在 site-specific page object 處理，不要複製整個 test flow。

# Site-specific implementation examples
以下為 `rc` 與 `lt` 兩個早期站台的實際差異對照，作為新站設計時的**典型差異模式參考**，不代表目前 repo 只有這兩站。設計新站時請：
1. 先查 `pages/factory.py` registry 確認當前已註冊站點。
2. 從下表挑選最接近新站行為的 pattern 作為起點。
3. 若新站行為完全不在下表中，補一條 pattern 並更新此 skill。

| 行為 | rc 站 | lt 站 |
|------|--------|--------|
| 登入入口 | Modal overlay，點擊按鈕開啟 | SPA `/login` 路由，直接導向 |
| 帳號 selector | `input[placeholder="用戶名"]` | `input.login-input` nth(0)（locale-agnostic） |
| 登入後等待 | Loading 動畫 (`img[alt="Loading"]`) | URL 離開 `/login`（SPA pushState） |
| 伺服器錯誤 | `toast-confirm-btn` 彈窗（MutationObserver 自動關閉） | 無此機制 |
| 用戶協議 | 首次登入出現，需點確定 | 無此機制 |
| 登出互動 | avatar dropdown → 登出按鈕 | hamburger drawer → `dispatch_event("click")` |
| overlay 攔截 | 無此問題 | drawer overlay（`fixed right-0`）常駐 DOM，closed 狀態仍攔截 pointer events，`click()` 永遠 timeout → 必須用 `dispatch_event("click")` |
| 多語系 | 固定繁中 | 5 語系，需 locale cookie 預設 |

# Refactor rules
1. 重構 page object 時，優先保持既有 public API 穩定，降低 test 修改量。
2. 若不得不調整 public method，需同步說明受影響測試檔與 conftest fixture。
3. 若重構涉及 visual regression 頁面，需提醒檢查 snapshot / reference screenshot 是否受影響。
4. 優先小步重構，不做無必要的大規模搬移。
5. 若只是單一測試使用的小互動，不要急著抽象成共用 helper。
6. 重構時需考慮未來站點擴充，而不是只讓現有站點變整齊。

# Anti-patterns
1. 在 test 裡直接複製大量 locator 與 click/fill 細節。
2. 把商業流程、assertion、locator 全塞進單一 page object method。
3. 為了統一而犧牲站台差異，導致共用層充滿 if/else。
4. 在 base class 中放大量 site-specific selector。
5. 建立命名模糊的 helper，例如 `handle_page()`、`process_flow()` 這類低語意方法。
6. 每新增一個站點就複製一整套 pages/tests 結構但不保留共通規則。
7. 直接 `from pages.rc.xxx import` 而不走 factory，導致 test 綁死特定站台。

# Output expectations
完成任務時，應：
- 說明新增或調整了哪些 page object / component object。
- 說明為何抽象、為何不抽象。
- 說明是否影響 `pages/factory.py` registry、conftest fixture 或 snapshot 邏輯。
- 若涉及新站點，說明其目錄放置策略與與既有站點的關係。
- 若變更 public API，列出所有受影響的 fixture 與 test 檔。
- 提供最小驗證指令，優先使用受影響範圍的 targeted pytest。
