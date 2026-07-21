"""
登入頁面 Page Object — rc 站點
Selector 來源：Chrome DevTools MCP 探索（見 .env SITE_RC_URL）
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present, wait_login_loading
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
        # SPA hydration 緩衝（2026-05-22 記錄的卡 /login 對策）：心跳走 WebSocket
        # 不擋 networkidle，HTTP 靜止即觸發；逾時不視為錯誤（best-effort）
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeoutError:
            pass
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

    def login(self, username: str, password: str, expect_success: bool = True):
        """填入帳號密碼並登入。

        expect_success=True（預設）：送出後守衛「表單真正關閉」，未關閉重送一次
        （SPA 卡 /login 對策）。負向測試（錯誤憑證，表單本來就會留著）必須傳
        False 跳過守衛，否則會被重送 + 最終 TimeoutError 誤傷。
        """
        sh = get_screenshotter(self.page)

        self.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.username_input, "fill_帳號")
        self.username_input.fill(username)

        self.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.password_input, "fill_密碼")
        self.password_input.fill(password)

        self.login_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_btn, "click_送出登入")
        self.login_btn.click()

        # 等待 loading 狗動畫（ALL_Loading.gif）出現後消失
        # 登入 API 回應期間會顯示此動畫，需等它消失才代表登入完成
        self._wait_for_loading()

        # 登入後可能出現伺服器錯誤彈窗
        dismiss_server_error_if_present(self.page)

        # 處理「用戶協議」彈窗（首次登入才會出現）
        self._handle_user_agreement()

        # 送出後等表單真正關閉（2026-07-21 連 3 次實錄：loading 跑完但表單仍在、
        # SPA 卡 /login 不轉場）。與 open_login_form 同類 hydration dead zone，
        # 修法對齊：未關閉 → 重送一次（同帳號重複送出無副作用）再等 10s。
        # 僅適用預期成功的登入；負向測試（expect_success=False）表單留著是正確結果。
        # 必須放在彈窗處理之後：CI fresh context 首登「協議確定」彈窗每次出現，
        # 彈窗未清前表單不會關（2026-07-21 CI 實錄）；retry 用「登入」文字限定
        # submit，避免與彈窗「確定」同為 primary-btn 的 strict violation。
        if expect_success:
            try:
                self.username_input.wait_for(state="hidden", timeout=10000)
            except PlaywrightTimeoutError:
                dismiss_server_error_if_present(self.page)
                self._handle_user_agreement()
                try:
                    self.username_input.wait_for(state="hidden", timeout=3000)
                except PlaywrightTimeoutError:
                    submit = self.page.locator("button.primary-btn", has_text="登入").first
                    if sh: sh.capture(submit, "click_送出登入_retry")
                    submit.click()
                    self._wait_for_loading()
                    dismiss_server_error_if_present(self.page)
                    self._handle_user_agreement()
                    self.username_input.wait_for(state="hidden", timeout=10000)

    def _wait_for_loading(self):
        """登入 loading 等待＋截圖：委派 utils.dialog_helper.wait_login_loading（RC/RD/RE 共用）"""
        wait_login_loading(self.page)

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
