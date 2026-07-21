"""
登入頁面 Page Object — re 站點 (BeWin)
與 rc 共用同一份 t9platform 平台 DOM 結構，但 selector 改用 CSS-based
（input.input-style + type）避開 placeholder 文案 i18n race（2026-05-24 baseline 觀察）。
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present, wait_login_loading
from utils.screenshot_helper import get_screenshotter


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

        # CSS-based locale-agnostic selectors（i18n hydration race 下 placeholder 可能短暫為空）
        self.username_input = page.locator('input.input-style[type="text"]')
        self.password_input = page.locator('input.input-style[type="password"]')
        self.login_btn = page.locator("button.primary-btn")
        self.login_trigger_btn = page.locator("button", has_text="登入").first

    def goto(self):
        """開啟首頁，並處理進站彈窗（伺服器錯誤 / 公告大圖輪播）

        - goto 改 domcontentloaded：dev 站有背景 WebSocket/心跳，load event 常不觸發。
        - helpers 會先用 count() 短路：元素不在 DOM → 立即回傳，不耗 timeout。
        """
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        dismiss_server_error_if_present(self.page)
        dismiss_announcement_popup_if_present(self.page)

    def open_login_form(self):
        """點擊右上角「登入」按鈕開啟登入表單

        wait 拉長至 15s：dev 站 SPA hydration + 登入 modal 動畫可能需時。
        trigger button 本身也要等：SPA 初始化完才會掛入 DOM。

        防 flaky：偶發第一次 click 沒觸發 modal（推測 hydration race），
        若 5s 內 username_input 未出現則再 click 一次。
        """
        sh = get_screenshotter(self.page)
        self.login_trigger_btn.wait_for(state="visible", timeout=15000)
        self.login_trigger_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_trigger_btn, "click_登入按鈕")
        self.login_trigger_btn.click()
        try:
            self.username_input.wait_for(state="visible", timeout=5000)
            return
        except PlaywrightTimeoutError:
            pass
        # Retry once：SPA hydration race 容忍
        if sh: sh.capture(self.login_trigger_btn, "click_登入按鈕_retry")
        self.login_trigger_btn.click()
        self.username_input.wait_for(state="visible", timeout=10000)

    def login(self, username: str, password: str):
        """填入帳號密碼並登入"""
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
        self._wait_for_loading()

        # 登入後可能出現伺服器錯誤彈窗
        dismiss_server_error_if_present(self.page)

        # 處理登入後可能出現的彈窗（用戶協議 / 警告等）
        self._handle_post_login_popup()

    def _wait_for_loading(self):
        """登入 loading 等待＋截圖：委派 utils.dialog_helper.wait_login_loading（RC/RD/RE 共用）"""
        wait_login_loading(self.page)

    def _handle_post_login_popup(self):
        """處理登入後可能出現的彈窗：
        - 「用戶協議」彈窗（首次登入時出現），自動按「確定」進站
        - 「警告」彈窗（密碼錯誤 / 帳號不存在），保留給測試自己斷言

        判斷邏輯：
        1. count() 短路：DOM 沒有「確定」按鈕直接 return（非首次登入常見路徑）
        2. 若同時偵測到「警告」標題，視為錯誤彈窗，**不**自動關閉
        3. 否則視為用戶協議彈窗，按下確定

        排除 toast-confirm-btn 是為了相容 RC 樣式的錯誤彈窗（有 toast-confirm-btn class）。
        """
        # 排除 toast-confirm-btn，避免誤關 RC 樣式的錯誤提示彈窗
        confirm_btn = self.page.locator("button:not(.toast-confirm-btn)", has_text="確定")
        if confirm_btn.count() == 0:
            return

        # RE 警告彈窗特徵：有「警告」標題 + 錯誤訊息文案
        # 若偵測到，視為錯誤彈窗，留給測試自己斷言，不點掉
        warning_indicators = self.page.locator("text=警告")
        if warning_indicators.count() > 0 and warning_indicators.first.is_visible():
            return

        try:
            confirm_btn.wait_for(state="visible", timeout=3000)
            sh = get_screenshotter(self.page)
            confirm_btn.scroll_into_view_if_needed()
            if sh: sh.capture(confirm_btn, "click_用戶協議確定")
            confirm_btn.click()
        except PlaywrightTimeoutError:
            pass  # 在 DOM 但未 visible（罕見），略過

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：開站 → 開登入表單 → 登入"""
        self.goto()
        self.open_login_form()
        self.login(username, password)
