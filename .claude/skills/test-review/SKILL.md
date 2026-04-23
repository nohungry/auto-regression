---
name: test-review
description: 審查 auto-regression repo 中的 pytest-playwright 測試、page objects、fixtures、與 visual regression 變更。當使用者要 code review 測試變更、檢查 PR diff、或請求審查測試品質與架構風險時，使用此 skill。
---

# Purpose
用於此 repo 的測試變更 review 工作，包含：
- 審查 pytest-playwright testcase 變更。
- 審查 page object / component object / fixture 調整。
- 檢查 visual regression baseline 與 reference screenshot 相關改動。
- 找出 flaky test、脆弱 selector、錯誤抽象與高風險 regression。
- 檢查變更是否仍適合未來 multi-site 擴充。

# Repo context
- 技術棧：Python + pytest-playwright。
- 多站台架構：`pages/factory.py` 使用 registry dict 依 `site_id` 路由對應 page object。
- 測試位於 `tests/<site_id>/`，page objects 位於 `pages/<site_id>/`。
- 每站有自己的 `tests/<site_id>/conftest.py`，覆寫 `site_config` 與站台特定 fixture。
- 全域 `conftest.py` 的 `_new_configured_page()` 注入 `toast-confirm-btn` MutationObserver（rc 站專有），其他站需在自己的 conftest 覆寫 `page` fixture 移除此注入。
- 截圖系統透過 `get_screenshotter(page)` 運作，POM 方法中應有截圖呼叫。
- LT 站目前採 **reference screenshot** 策略：輸出至 `screenshots/lt/vr_reference/` 供人工確認，不做 pixel 比對（跨環境無法穩定）。`tests/lt/__snapshots__/` 為舊 baseline，無測試引用。
- 未來站點會增加，review 需同時評估結構可延伸性。

# Review priorities
1. **correctness**：變更是否真的符合測試意圖。
2. **reliability**：是否引入 flaky wait、脆弱 selector、隱性 race condition。
3. **architecture**：是否破壞既有 multi-site / POM / factory 結構。
4. **maintainability**：是否新增重複 flow、命名混亂、難以維護的 helper。
5. **scalability**：是否把目前兩站寫死，導致未來新增站點時難以擴充。
6. **regression risk**：是否影響 `conftest.py`、`pages/factory.py`、snapshot baseline、跨站共用行為。

# Review checklist — common pitfalls
以下為此 repo 已知的高頻問題，review 時應逐項檢查：

## Selector 問題
- [ ] 是否使用 locale-agnostic selector？lt 站有 5 語系，不可綁死 placeholder / button text。
- [ ] 是否誤用 `.first()` / `.last()` 當 method call？Python Playwright 中這是 property，寫成 `.first()` 會觸發 `__call__` 錯誤。
- [ ] 是否用 `text=XXX` 命中了 hidden sidebar node？rc 站的 `.text-black` sidebar label 與 content 同文案，需用 `:not(.text-black)` 排除。
- [ ] 是否對多語系站台使用了 `get_by_placeholder()` 或 `get_by_role(name=...)` 綁死特定語言？

## Interaction 問題
- [ ] 是否在 click/fill 前呼叫 `scroll_into_view_if_needed()`？
- [ ] 是否對 viewport 外元素（CSS hidden sidebar、lt drawer 按鈕）改用 `dispatch_event("click")`？
- [ ] 是否對被 overlay backdrop 攔截的元素改用 `dispatch_event("click")`？overlay 常駐 DOM 時（如 lt drawer，closed 狀態仍 `fixed right-0` 攔截點擊），`click()` 會永遠 timeout，需改用 `dispatch_event`。
- [ ] 是否在 DOM re-render 後對舊 locator 呼叫 `scroll_into_view_if_needed()`？應改用 `page.evaluate("window.scrollBy(0, N)")`。
- [ ] 是否出現裸 `time.sleep()` 或不必要的 hard wait？
- [ ] lt 站是否在 goto `/login` 時使用 `wait_until="networkidle"`？SPA 表單需等完全初始化。

## Fixture 問題
- [ ] 是否正確選用 fixture scope？smoke → `page`/`logged_in_page`（function）；functional → `class_logged_in_page` + `go_home`（class）。
- [ ] 是否任意新增 fixture 名稱？應優先沿用既有命名。
- [ ] 新站的 `tests/<site_id>/conftest.py` 是否覆寫了 `site_config`？
- [ ] 新站是否評估了全域 `page` fixture 的 MutationObserver 注入是否適用？不適用需覆寫。
- [ ] 若覆寫了 `page` fixture，`class_logged_in_page` 是否也需一併處理？

## Factory / POM 問題
- [ ] test 檔是否直接 `from pages.<site_id>.xxx import` 而不走 factory？
- [ ] 新增站點是否已在 `factory.py` 的 registry dict 中註冊？
- [ ] 新增 page type 是否有對應的 registry 與 getter function？
- [ ] page object 的 public API 是否維持一致？(`goto_and_login`、`verify_logged_in`、`verify_login_success`、`dismiss_any_popups`、`is_logged_in`、`logout`)
- [ ] fixture 層與「只需確認已登入狀態」的測試是否用 `verify_logged_in()`（輕量無副作用），而非 `verify_login_success()`（可能含 drawer/reload 副作用）？

## Screenshot 問題
- [ ] 新增的 POM 方法是否有 `get_screenshotter()` 截圖呼叫？
- [ ] label 是否遵守命名規則（`click_`/`fill_`/`verify_`/`loading_`）？
- [ ] 是否使用 `if sh:` guard 避免 helper 不存在時報錯？
- [ ] **截圖位置是否在 `assert` / `expect(...)` / 可能拋例外的 helper 呼叫「之前」？** 反模式：`assert ...; if sh: sh.full_page(...)` — 失敗路徑拋 AssertionError 後，後面那行 sh 永遠不會執行，per-test 資料夾會是空的，無法佐證失敗現場。對 `xfail(strict=True)` 的守門 test 尤其嚴重（每次跑都 fail，永遠沒證據）。正確模式：先 `if sh: sh.full_page(...)`，再 `assert ...`。
- [ ] 若是 xfail / 守門 test，label 是否採中性命名（不承諾 pass/fail，例如 `verify_首頁破圖檢測_total{n}_broken{k}`，而非 `verify_首頁無破圖` 或 `verify_登入成功`）？label 帶 pass 語意會讓 README.md 讀者以為這是 pass 現場。
- [ ] 若 test 只用 `_save(...)` / `save_vr_screenshot(...)` 寫到 `vr_reference/`，per-test 資料夾會是空的。是否在 test body 另外呼叫 `sh.full_page(...)` 在 per-test 資料夾留一份？（導航類 test 建議 pre/post navigation 各留一張，確保 helper fail 仍有證據）
- [ ] **動態值欄位**（balance / username / 訂單號 / 時間戳等會隨時間或帳號變動的值）若只驗「非空」或「格式正確」而非「等於特定值」:
  - test docstring 是否寫明斷言策略（例如「只驗非空，不寫死數值」）？
  - screenshot label 是否帶「**非空**」「**格式**」等關鍵字（如 `verify_XXX非空_{value}`）？若 label 只帶值沒帶策略，reviewer 看 README.md 會誤以為是寫死比對。

## Visual regression 問題
- [ ] 是否誤對動態內容頁做 pixel-level snapshot assertion？LT 應只存 reference screenshot 供人工確認。
- [ ] 若動到 `tests/lt/feature/visual/` 下的測試，是否維持「存檔不比對」的 reference screenshot 模式？
- [ ] 若動到 `tests/lt/__snapshots__/`（legacy baseline），是否能直接刪除，或有保留理由？

# High-risk change rules
1. 下列變更需特別提高警覺：`conftest.py`、`pages/factory.py`、snapshot baseline、fixture 新增/更名/行為變更、visual regression assertion 調整。
2. 若 PR 含 snapshot 更新，需要求說明為何屬於產品預期變更。
3. 若 PR 同時改 page object API 與多個 tests，需檢查是否有隱性破壞或未覆蓋流程。
4. 若共用 helper（`utils/dialog_helper.py`、`utils/screenshot_helper.py`、`utils/locale_helper.py`）被修改，需評估是否波及所有既有與未來站點使用方式。
5. 若新增站點，需檢查是否完整走完 onboarding checklist：`.env` → `pages/<site_id>/` → `factory.py` registry → `tests/<site_id>/conftest.py` → `pytest.ini` markers。

# Review comment rules
1. 先指出 blocking issues，再指出 non-blocking improvements。
2. 評論需具體，指出檔案、行號、風險、原因與建議修法。
3. 若變更可接受但仍有 trade-off，應明確註明風險而非直接否定。
4. 若沒有明顯問題，也要簡短說明為何風險可控。
5. 不要只做風格 nitpick 而忽略 flaky、regression 與擴展性風險。

# Output expectations
review 結果應包含：
- **Blocking issues**（若有）：附檔案路徑、問題描述、建議修法。
- **Non-blocking improvements**（若有）：附具體建議。
- **受影響範圍與風險摘要**：哪些 fixture / 站點 / snapshot 可能受波及。
- **Multi-site 擴展性評估**：是否把現況寫死，或結構可延伸。
- **建議驗證指令**：targeted pytest 為主，指定到檔案或 marker 層級。
