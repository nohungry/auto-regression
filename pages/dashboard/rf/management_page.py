"""
後台管理頁 Page Object — RF 站點（金爺娛樂城，信用版）

範圍：read-only 導航 + logout + 存入/提取（站長帳號 qatest03 操作）。
同時支援站長與代理兩種帳號層級。

實機 probe 關鍵事實（2026-06-17 ~ 2026-06-18）：

站長層級（qatest03）：
- 登入後落點 `#/management/all-management`，側欄 class=`sidebar`（無 hide）。
- 頂層選單 `.sidebar-nav li.parent-li` 共 9 項（含修改密碼/登出）；
  路由選單 7 項：儀表板/管理/報表/其它設定/遊戲管理/後臺權限/後臺紀錄。
- 葉節點有 href（`a[href^='#/...']`），可 dispatch_event("click") + wait_for_url 導航。
- 「登出」為 `li.parent-li` 內 `a.memberSpan`，`display: none`（必須 dispatch_event）。

代理層級（qaautodrf）：
- 登入後落點 `#/management/all-management`，側欄 class=`sidebar`（無 hide）。
- 頂層選單 4 項：管理/報表/修改密碼/登出。
- 報表有 href 子項（agentRevenueSplit/quota-history/agent-history），可直接 dispatch。
- 管理無 href 子項（僅父項，點父項 a.memberSpan dispatch_event 即可導向）。

共用：
- 登入成功信號：`.sidebar-nav` first attached。
- 內容容器：`.container-view`（導航後 visible）。
- 登出：`.sidebar-nav li.parent-li` 含「登出」文字的 `a.memberSpan`，dispatch_event("click")。

充提相關 probe 事實（2026-06-18）：
- 會員列表為 `.tab-item` 結構（非 table/tr），站長帳號下顯示全站會員。
- 設每頁 500 筆可讓 drfauto01（第 40 筆）在 DOM 中出現（不需搜尋框）。
- 無帳號搜尋框；頁面僅有 multiselect 代理選擇器（不用）。
- 每個 .tab-item 含 HTML attribute `balance="..."` 儲存額度（穩定讀法，無格式問題）。
- 存入按鈕：`button.btn-primary.me-2`（第一個），提取：`button.btn-primary`（無 me-2）。
- 存入/提取 dialog class：`.dialog-container.bottom-style`。
- 金額 input：dialog 內唯一的 `input[type='text']`（無 class、無 placeholder）。
- 送出按鈕：`button.primary-button`，取消：`button.secondary-button`。
- RF 後台無操作者密碼欄位（不同於 RC 站）。
- 等待 dialog 關閉：`.dialog-container.bottom-style` 消失（hidden/detached）。
"""

import re

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from utils.screenshot_helper import get_screenshotter


class ManagementPage:

    def __init__(self, page: Page):
        self.page = page
        self.sidebar = page.locator(".sidebar-nav")
        self.parent_items = page.locator(".sidebar-nav li.parent-li")
        self.content = page.locator(".container-view")
        # 登出：sidebar 中文案含「登出」的 parent-li 下的 a.memberSpan（display:none → dispatch）
        self.logout_link = page.locator(".sidebar-nav li.parent-li").filter(
            has_text="登出"
        ).locator("a.memberSpan")

    def sidebar_item_count(self) -> int:
        """頂層選單（li.parent-li）數量；先等側欄掛上 DOM。"""
        self.sidebar.first.wait_for(state="attached", timeout=15000)
        return self.parent_items.count()

    def parent_route_ids(self) -> list:
        """回傳頂層選單的 route id 清單（父項 `a.memberSpan` 的 id，如 '/management'）。
        locale-agnostic：id 是 route 不是文案，可穩定比對權限/可見選單。
        id 為空代表非路由項目（如「修改密碼」「登出」沒有 route id）。
        """
        self.sidebar.first.wait_for(state="attached", timeout=15000)
        spans = self.page.locator(".sidebar-nav li.parent-li a.memberSpan")
        return [spans.nth(i).get_attribute("id") for i in range(spans.count())]

    def navigate(self, route_substr: str):
        """點側欄葉節點導航到含 route_substr 的頁面。

        RF 葉節點為 `a[href^='#/...']`，`display: none` 或在縮合選單內，
        需 dispatch_event("click") 觸發 SPA 路由。
        以 URL hash 變化 + .container-view visible 作為導航成功判定（結構性，不綁文案）。
        """
        sh = get_screenshotter(self.page)
        link = self.page.locator(f"a[href*='{route_substr}']").first
        link.wait_for(state="attached", timeout=10000)
        link.dispatch_event("click")
        self.page.wait_for_url(f"**{route_substr}**", timeout=15000)
        self.content.first.wait_for(state="visible", timeout=15000)
        if sh:
            sh.full_page(f"verify_導航_{route_substr.replace('/', '_')}")

    def logout(self):
        """登出 → 回 #/login（登入表單重現）。

        登出連結（a.memberSpan in 登出 parent-li）為 display:none，
        需 dispatch_event("click") 直接觸發 DOM event。
        """
        sh = get_screenshotter(self.page)
        self.logout_link.first.wait_for(state="attached", timeout=10000)
        if sh:
            sh.capture(self.logout_link.first, "click_登出")
        self.logout_link.first.dispatch_event("click")
        self.page.wait_for_url("**/login**", timeout=15000)
        self.page.locator("input[type='password']").first.wait_for(
            state="visible", timeout=15000
        )
        if sh:
            sh.full_page("verify_登出回登入頁")

    # -----------------------------------------------
    # 充提相關方法（probe 2026-06-18 確認）
    # -----------------------------------------------

    def switch_to_member_tab(self):
        """切換到 container-management 的「會員」tab。

        頁面共有 6 個 button.tab-btn（代理/會員/子帳號 × 2 組）。
        前 3 個屬於 .tabs-search（左側代理搜尋），後 3 個屬於 .container-management（主內容）。
        找所有 visible button.tab-btn，第 5 個（index 4，0-based）為主內容區的「會員」tab。
        """
        sh = get_screenshotter(self.page)
        tab_btns = self.page.locator("button.tab-btn")

        # 等待 tab 渲染完成
        tab_btns.first.wait_for(state="visible", timeout=15000)

        # 取所有 visible tab，選 index 4（主內容區的會員 tab）
        visible_handles = [
            tab_btns.nth(i).element_handle()
            for i in range(tab_btns.count())
            if tab_btns.nth(i).is_visible()
        ]

        if len(visible_handles) < 5:
            raise RuntimeError(
                f"找不到足夠的 tab-btn（預期 ≥5 個 visible，實際 {len(visible_handles)} 個）"
            )

        if sh:
            sh.full_page("click_切換會員Tab_before")

        # JS click 觸發 Vue event handler（index 4 = 主內容區的「會員」tab）
        self.page.evaluate("(el) => el.click()", visible_handles[4])
        self._wait_for_list_loaded()

        if sh:
            sh.full_page("click_切換會員Tab_after")

    def set_page_size(self, size: int = 500):
        """設定每頁顯示筆數（select 選項含 10/20/50/100/200/500）。

        RF 後台 drfauto01 為第 40 筆，設 500 確保在 DOM 中可見。
        用 JS 直接設定 select value 並 dispatch change event（Vue reactive）。
        """
        self.page.evaluate(
            "(size) => {"
            "  var selects = document.querySelectorAll('select');"
            "  for (var i = 0; i < selects.length; i++) {"
            "    var opts = Array.from(selects[i].options).map(function(o){ return o.value; });"
            "    if (opts.indexOf(String(size)) >= 0) {"
            "      selects[i].value = String(size);"
            "      selects[i].dispatchEvent(new Event('change', { bubbles: true }));"
            "      break;"
            "    }"
            "  }"
            "}",
            size,
        )
        self._wait_for_list_loaded()

    def _find_member_tab_item(self, account: str):
        """找到含指定帳號的 .tab-item locator。

        RF 後台不提供帳號搜尋框；改為設大每頁筆數（500）後，
        用 locator filter 直接在 .tab-item 列表中找帳號。
        回傳 Locator（count 為 1 時確認找到）。
        """
        item = self.page.locator(".tab-item").filter(has_text=account)
        item.first.wait_for(state="attached", timeout=15000)
        return item.first

    def get_member_balance(self, account: str) -> float:
        """讀取指定會員的當前額度（balance）。

        策略：打開會員的「存入」dialog → 讀 dialog 中「會員剩餘餘額」span.label-xs
             → 點取消關閉 dialog。
        此 dialog 中的值為後端實時值（非 tab-item 的渲染快照）。

        架構說明（probe 2026-06-18）：
        dialog HTML 結構：
          <p class="info">
            <span class="label-m">會員帳號 :</span>
            <span class="label-m highlight">drfauto01(drfauto01)</span>
            <span class="label-s highlight">剩餘餘額</span>
            <span class="label-xs">{balance}</span>
          </p>
        取第二個 p.info 的 span.label-xs（第一個 p.info 是代理資訊）。
        """
        sh = get_screenshotter(self.page)

        tab_item = self._find_member_tab_item(account)
        tab_item.scroll_into_view_if_needed()

        # 點存入按鈕（打開 dialog 讀 balance，不填金額不送出）
        deposit_btn = tab_item.locator("button.btn-primary.me-2").first
        deposit_btn.wait_for(state="attached", timeout=5000)
        self.page.evaluate("(el) => el.click()", deposit_btn.element_handle())
        self.page.wait_for_timeout(800)

        # 取 dialog 中的會員剩餘餘額（第二個 p.info 的 span.label-xs）
        dialog_last = self.page.locator(".dialog-container.bottom-style").last
        dialog_last.wait_for(state="attached", timeout=8000)

        # 從 dialog 讀取會員餘額（dialog 中有兩個 span.label-xs：代理餘額和會員餘額）
        # 第二個 span.label-xs 是會員餘額
        balance_text = self.page.evaluate(
            "function() {"
            "  var dialogs = document.querySelectorAll('.dialog-container.bottom-style');"
            "  var dialog = dialogs[dialogs.length-1];"
            "  if (!dialog) return null;"
            "  var spans = dialog.querySelectorAll('.label-xs');"
            "  return spans.length >= 2 ? spans[1].textContent.trim() : null;"
            "}"
        )

        if sh:
            sh.full_page(f"verify_會員額度非空_{account}_{balance_text}")

        # 關閉 dialog（點取消）
        self.page.evaluate(
            "function() {"
            "  var dialogs = document.querySelectorAll('.dialog-container.bottom-style');"
            "  var dialog = dialogs[dialogs.length-1];"
            "  if (!dialog) return;"
            "  var cancelBtn = dialog.querySelector('button.secondary-button');"
            "  if (cancelBtn) cancelBtn.click();"
            "}"
        )
        self.page.wait_for_timeout(500)

        if balance_text is None:
            raise ValueError(f"無法從 {account} 的存入 dialog 讀取剩餘餘額")

        # 去除千分位逗號轉 float
        balance = float(balance_text.replace(",", ""))
        return balance

    def deposit(self, account: str, amount: int):
        """對指定會員執行存入操作。

        流程：找到 .tab-item → 點 button.btn-primary.me-2（存入）
             → dialog .dialog-container.bottom-style 出現
             → 填金額（Vue-safe JS fill + input/change event）
             → 點 button.primary-button（送出）→ 等 dialog 關閉。

        RF 後台無操作者密碼欄位（probe 2026-06-18 確認）。
        存入後需重新載入列表（reload_management_page）讓 balance attribute 更新。
        """
        sh = get_screenshotter(self.page)

        tab_item = self._find_member_tab_item(account)
        tab_item.scroll_into_view_if_needed()

        deposit_btn = tab_item.locator("button.btn-primary.me-2").first
        deposit_btn.wait_for(state="attached", timeout=5000)

        if sh:
            sh.capture(deposit_btn, f"click_存入_{account}_{amount}")

        self.page.evaluate("(el) => el.click()", deposit_btn.element_handle())

        self._fill_topup_dialog(amount, "存入")

        if sh:
            sh.full_page(f"verify_存入完成_{account}_{amount}")

    def withdraw(self, account: str, amount: int):
        """對指定會員執行提取操作。

        流程：找到 .tab-item → 點 button.btn-primary（無 me-2，提取）
             → dialog .dialog-container.bottom-style 出現
             → 填金額（Vue-safe JS fill）→ 點 button.primary-button（送出）
             → 等 dialog 關閉。

        RF 後台無操作者密碼欄位。
        提取後需重新載入列表讓 balance attribute 更新。
        """
        sh = get_screenshotter(self.page)

        tab_item = self._find_member_tab_item(account)
        tab_item.scroll_into_view_if_needed()

        # 提取按鈕：btn-primary 但不含 me-2（CSS specificity 分開）
        # 用 :not(.me-2) filter 排除存入按鈕
        withdraw_btn = tab_item.locator("button.btn-primary:not(.me-2)").first
        withdraw_btn.wait_for(state="attached", timeout=5000)

        if sh:
            sh.capture(withdraw_btn, f"click_提取_{account}_{amount}")

        self.page.evaluate("(el) => el.click()", withdraw_btn.element_handle())

        self._fill_topup_dialog(amount, "提取")

        if sh:
            sh.full_page(f"verify_提取完成_{account}_{amount}")

    def reload_management_page(self, dashboard_url: str):
        """重新載入後台管理頁，讓 .tab-item 的 balance attribute 從後端刷新。

        RF 後台存入/提取後，會員 tab 的 .tab-item 不會自動更新 balance attribute，
        需要重新 goto 管理頁觸發列表重新渲染。
        """
        self.page.goto(
            f"{dashboard_url}#/management/all-management",
            wait_until="domcontentloaded",
        )
        self.page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=15000)
        self._wait_for_list_loaded()

    def _fill_topup_dialog(self, amount: int, operation: str):
        """填寫存入/提取 dialog（RF 後台版）。

        dialog class：.dialog-container.bottom-style
        金額 input：dialog 內唯一的 input[type='text']（is_visible=True，可 Playwright fill）
        送出按鈕：button.primary-button（is_visible=True，可 click(force=True)）
        取消按鈕：button.secondary-button

        RF 後台無操作者密碼欄位，不同於 RC/RE 站。

        架構說明（probe 2026-06-18）：
        - 每個 .tab-item 有一個常駐 hidden 的 .dialog-container.bottom-style。
        - 點擊存入/提取按鈕後，Vue 動態新增一個全局 visible dialog（最後一個，index +1）。
        - Playwright .is_visible() 對 dialog 容器回報 False（祖先 overflow 誤判），
          但 dialog 內的 input 和 button 本身 is_visible=True，可直接操作。
        - 解法：用 .last 取最後新增的 dialog，input 用 fill(force=True)，
          submit_btn 用 click(force=True)，無需 JS 繞過。
        """
        sh = get_screenshotter(self.page)

        # 等新的 dialog 的 primary-button 掛上（動態新增，為最後一個）
        submit_btn_global = self.page.locator("button.primary-button").last
        submit_btn_global.wait_for(state="attached", timeout=10000)
        self.page.wait_for_timeout(300)  # 等 Vue 完成 reactive 掛載

        # 取最後一個 dialog（就是動態新增的那個）
        dialog_last = self.page.locator(".dialog-container.bottom-style").last

        if sh:
            sh.full_page(f"dialog_{operation}_opened")

        # 找 dialog 內的金額 input（is_visible=True，可 Playwright fill）
        amount_input = dialog_last.locator("input[type='text']").last
        amount_input.wait_for(state="attached", timeout=5000)

        if sh:
            sh.full_page(f"fill_{operation}_金額_{amount}_pre")

        # Playwright fill + force=True（input is_visible=True；force 確保 actionability 通過）
        amount_input.fill(str(amount), force=True)

        if sh:
            sh.full_page(f"fill_{operation}_金額_{amount}")

        # 送出按鈕（is_visible=True，click(force=True) 繞過祖先容器 overflow 誤判）
        submit_btn = dialog_last.locator("button.primary-button").last
        submit_btn.wait_for(state="attached", timeout=5000)

        if sh:
            sh.full_page(f"click_{operation}_送出_pre")

        submit_btn.click(force=True)

        # 等送出後 dialog 消失（primary-button 被移除）
        try:
            submit_btn_global.wait_for(state="hidden", timeout=15000)
        except PlaywrightTimeoutError:
            pass

        self._wait_for_list_loaded()

        if sh:
            sh.full_page(f"verify_{operation}_dialog已關閉")

    def _wait_for_list_loaded(self):
        """等待列表載入完成（loading mask 消失 + DOM 穩定）。"""
        try:
            loading = self.page.locator(".el-loading-mask, .loading, [class*='loading']")
            loading.wait_for(state="hidden", timeout=8000)
        except PlaywrightTimeoutError:
            pass
        self.page.wait_for_timeout(800)
