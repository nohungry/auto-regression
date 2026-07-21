"""
登入頁面 Page Object — rd 站點 (狗狗娛樂城)
與 rc/re 同 t9platform 平台，但 selector 與文案有差異：
- placeholder 用「帳號」（rc/re 用「用戶名」）
- submit button 用 button.main-btn（rc/re 用 button.primary-btn）
- trigger button 文案用「登錄」（rc/re 用「登入」）
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present, dismiss_dialog_mask_if_present, wait_login_loading
from utils.screenshot_helper import get_screenshotter


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

        # Selectors（RD 特有）
        self.username_input = page.locator('input[placeholder="帳號"]')
        self.password_input = page.locator('input[placeholder="密碼"]')
        # main-btn 在 RD 首頁有兩個（modal 「登錄」 + navbar 「下載」），用 has_text 區分
        self.login_btn = page.locator("button.main-btn", has_text="登錄")
        self.login_trigger_btn = page.locator("button", has_text="登錄").first

    def goto(self):
        """開啟首頁，並處理進站彈窗（伺服器錯誤 / 公告大圖輪播）

        - goto 改 domcontentloaded：dev 站有背景 WebSocket/心跳，load event 常不觸發。
        - helpers 會先用 count() 短路：元素不在 DOM → 立即回傳，不耗 timeout。
        """
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        dismiss_server_error_if_present(self.page)
        dismiss_announcement_popup_if_present(self.page)

    def open_login_form(self):
        """點擊右上角「登錄」按鈕開啟登入表單

        wait 拉長至 15s：dev 站 SPA hydration + 登入 modal 動畫可能需時。

        RD 特殊：dialog-mask 蓋板廣告（z-9999）攔截 pointer events，
        必須用 dispatch_event("click") 觸發 DOM event 繞過 playwright actionability check
        （見 CLAUDE.md「已知互動例外」章節 — 常駐 overlay backdrop 攔截點擊的 pattern）。

        防 flaky：偶發第一次 click 沒觸發 modal（推測 hydration race），
        若 5s 內 username_input 未出現則再 dispatch 一次。
        """
        sh = get_screenshotter(self.page)
        self.login_trigger_btn.wait_for(state="visible", timeout=15000)
        if sh: sh.capture(self.login_trigger_btn, "click_登錄按鈕")
        self.login_trigger_btn.dispatch_event("click")
        try:
            self.username_input.wait_for(state="visible", timeout=5000)
            return
        except PlaywrightTimeoutError:
            pass
        # Retry once：SPA hydration race 容忍
        if sh: sh.capture(self.login_trigger_btn, "click_登錄按鈕_retry")
        self.login_trigger_btn.dispatch_event("click")
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

        # 同 trigger button：modal 內 submit 也被 dialog-mask 攔截 pointer events
        # 用 dispatch_event 繞過 actionability check
        if sh: sh.capture(self.login_btn, "click_送出登錄")
        self.login_btn.dispatch_event("click")

        # 等待 loading 動畫出現後消失
        self._wait_for_loading()

        # 登入後可能出現伺服器錯誤彈窗
        dismiss_server_error_if_present(self.page)

        # 處理登入後可能出現的彈窗
        self._handle_post_login_popup()

    def _wait_for_loading(self):
        """登入 loading 等待＋截圖：委派 utils.dialog_helper.wait_login_loading（RC/RD/RE 共用）"""
        wait_login_loading(self.page)

    def _handle_post_login_popup(self):
        """處理登入後可能出現的彈窗（用戶協議 / 警告）

        判斷邏輯（沿用 RE）：
        1. count() 短路：DOM 沒有「確定」按鈕直接 return
        2. 若同時偵測到「警告」標題，視為錯誤彈窗，不自動關閉
        3. 否則視為用戶協議彈窗，按下確定

        排除 toast-confirm-btn 是為了相容 RC 樣式的錯誤彈窗。
        """
        confirm_btn = self.page.locator("button:not(.toast-confirm-btn)", has_text="確定")
        if confirm_btn.count() == 0:
            return

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
            pass

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：開站 → 開登入表單 → 登入"""
        self.goto()
        self.open_login_form()
        self.login(username, password)
