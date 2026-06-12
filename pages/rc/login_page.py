"""
登入頁面 Page Object — rc 站點
Selector 來源：Chrome DevTools MCP 探索（見 .env SITE_RC_URL）
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present
from utils.screenshot_helper import get_screenshotter


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

        # Selectors
        self.username_input = page.locator('input[placeholder="用戶名"]')
        self.password_input = page.locator('input[placeholder="密碼"]')
        self.login_btn = page.locator("button.primary-btn")
        self.login_trigger_btn = page.locator("button", has_text="登入").first

    def goto(self):
        """開啟首頁，並處理進站彈窗（伺服器錯誤 / 公告大圖輪播）

        - goto 改 domcontentloaded：dev-rc 有背景 WebSocket/心跳，load event 常不觸發。
        - helpers 會先用 count() 短路：元素不在 DOM → 立即回傳，不耗 timeout。
        """
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        dismiss_server_error_if_present(self.page)
        dismiss_announcement_popup_if_present(self.page)

    def open_login_form(self):
        """點擊右上角「登入」按鈕開啟登入表單

        SPA hydration race（dev-rc 實機 probe 2026-05-09）：
        - 「登入」button 在 ~1s 即 visible 進入 DOM
        - 但 click handler 約在 3.3s-5.3s 才綁定完成（依 hydration 進度）
        - 在 dead zone 內 click 完全不會觸發 modal（無錯誤訊息，靜默失敗）

        Luke 原本「click → 等 5s → 重試 1 次」邊界踩在 hydration 邊緣，
        dev-rc 慢一點就會兩次 click 都落在 dead zone。

        修法：retry loop — click → 短等 1.5s → 沒 modal 就再 click。
        最多 10 次（≈ 15s 預算），覆蓋 hydration 變異。
        實機觀察 typical 案例 1-3 次 click 即成功。

        popup-announcement-mask（PR #30）已用 CSS rule 永久 kill，無需 dismiss。
        """
        sh = get_screenshotter(self.page)
        self.login_trigger_btn.wait_for(state="visible", timeout=15000)

        # 確保即使 popup 在 goto 後才出現，也已被 CSS killer 注入過
        dismiss_announcement_popup_if_present(self.page)

        self.login_trigger_btn.scroll_into_view_if_needed()

        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            # 第 1 次與最後 1 次必拍照；中間 retry 留 trace 但減量
            if sh and (attempt == 1 or attempt == max_attempts):
                label = "click_登入按鈕" if attempt == 1 else f"click_登入按鈕_attempt{attempt}"
                sh.capture(self.login_trigger_btn, label)
            self.login_trigger_btn.click()
            try:
                self.username_input.wait_for(state="visible", timeout=1500)
                if sh and attempt > 1:
                    sh.capture(self.username_input, f"verify_modal_開啟_於attempt{attempt}")
                return  # modal opened
            except PlaywrightTimeoutError:
                continue  # handler 可能未綁定，再試
        # 10 次仍 fail → 拋最終錯誤（含完整 timeout 訊息給 debug 用）
        self.username_input.wait_for(state="visible", timeout=5000)

    def login(self, username: str, password: str):
        """填入帳號密碼並送出登入。

        SPA hydration race 強化（dev-rc 偶發「submit 後卡 /login、avatar 不出現」）：
        送出按鈕的 click handler 與 open_login_form 的 trigger 同樣有 hydration dead zone，
        click 可能靜默無效、SPA 不離開登入表單。改為「submit → 等登入表單消失 → 沒消失就重 submit」，
        最多 3 次。成功信號＝用戶名 input 變 hidden（登入生效、表單關閉 / 離開登入頁）。
        """
        sh = get_screenshotter(self.page)

        self.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.username_input, "fill_帳號")
        self.username_input.fill(username)

        self.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.password_input, "fill_密碼")
        self.password_input.fill(password)

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                self.login_btn.scroll_into_view_if_needed()
                if sh and (attempt == 1 or attempt == max_attempts):
                    label = "click_送出登入" if attempt == 1 else f"click_送出登入_retry{attempt}"
                    sh.capture(self.login_btn, label)
                self.login_btn.click(timeout=5000)
            except PlaywrightTimeoutError:
                pass  # 送出按鈕已消失 → 可能已登入成功（表單關閉），交給下方成功檢查

            # 登入 API 回應期間會顯示 loading 狗動畫（ALL_Loading.gif），等它出現後消失
            self._wait_for_loading()
            dismiss_server_error_if_present(self.page)
            self._handle_user_agreement()

            # 成功信號：登入表單（用戶名 input）消失即代表登入生效、離開登入頁
            try:
                self.username_input.wait_for(state="hidden", timeout=5000)
                return
            except PlaywrightTimeoutError:
                # 表單仍在 → submit 落在 hydration dead zone、沒生效。重填欄位後重試 submit。
                if attempt < max_attempts:
                    try:
                        self.username_input.fill(username)
                        self.password_input.fill(password)
                    except PlaywrightTimeoutError:
                        pass  # 欄位已不在（慢速成功）→ 下一輪 click 的 except 會處理
                    continue
        # 3 次仍未離開登入表單 → 不在此拋錯，維持原行為（login() 不自行斷言），
        # 交由下游 verify_logged_in / verify_login_success 給出含截圖的明確失敗。

    def _wait_for_loading(self):
        """
        等待 loading 狗動畫（img[alt="Loading"] / ALL_Loading.gif）出現並消失。
        Loading overlay: div.fixed.inset-0.z-[9999]，包含 ALL_Loading.gif。
        若 2 秒內未出現（登入失敗或速度極快）則略過。
        """
        sh = get_screenshotter(self.page)
        loading_img = self.page.locator('img[alt="Loading"]')
        try:
            loading_img.wait_for(state="visible", timeout=2000)
            if sh: sh.capture(loading_img, "loading_登入中")
            loading_img.wait_for(state="hidden", timeout=10000)
            if sh: sh.full_page("loading_完成_進入首頁")
        except PlaywrightTimeoutError:
            pass  # loading 未出現或已快速消失，略過

    def _handle_user_agreement(self):
        """處理用戶協議彈窗（若出現則點確定）

        先用 count() 短路：非首次登入 DOM 不會有此按鈕，立即略過不耗 timeout。
        """
        # 排除 toast-confirm-btn，避免誤關錯誤提示彈窗
        agreement_btn = self.page.locator("button:not(.toast-confirm-btn)", has_text="確定")
        if agreement_btn.count() == 0:
            return
        try:
            agreement_btn.wait_for(state="visible", timeout=3000)
            sh = get_screenshotter(self.page)
            agreement_btn.scroll_into_view_if_needed()
            if sh: sh.capture(agreement_btn, "click_用戶協議確定")
            agreement_btn.click()
        except PlaywrightTimeoutError:
            pass  # 在 DOM 但未 visible（罕見），略過

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：開站 → 開登入表單 → 登入"""
        self.goto()
        self.open_login_form()
        self.login(username, password)
