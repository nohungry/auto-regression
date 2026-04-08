"""
登入頁面 Page Object — drc 站點
Selector 來源：Chrome DevTools MCP 探索 dev-drc.t9platform-ph.com
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
        """開啟首頁，並處理進站彈窗（伺服器錯誤 / 公告大圖輪播）"""
        self.page.goto(self.base_url)
        self.page.wait_for_load_state("networkidle")
        dismiss_server_error_if_present(self.page)
        dismiss_announcement_popup_if_present(self.page, timeout=5000)

    def open_login_form(self):
        """點擊右上角「登入」按鈕開啟登入表單"""
        sh = get_screenshotter(self.page)
        self.login_trigger_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_trigger_btn, "click_登入按鈕")
        self.login_trigger_btn.click()
        self.username_input.wait_for(state="visible", timeout=5000)

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
        # 登入 API 回應期間會顯示此動畫，需等它消失才代表登入完成
        self._wait_for_loading()

        # 登入後可能出現伺服器錯誤彈窗
        dismiss_server_error_if_present(self.page)

        # 處理「用戶協議」彈窗（首次登入才會出現）
        self._handle_user_agreement()

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
        """處理用戶協議彈窗（若出現則點確定）"""
        try:
            # 排除 toast-confirm-btn，避免誤關錯誤提示彈窗
            agreement_btn = self.page.locator("button:not(.toast-confirm-btn)", has_text="確定")
            agreement_btn.wait_for(state="visible", timeout=3000)
            sh = get_screenshotter(self.page)
            agreement_btn.scroll_into_view_if_needed()
            if sh: sh.capture(agreement_btn, "click_用戶協議確定")
            agreement_btn.click()
        except PlaywrightTimeoutError:
            pass  # 非首次登入不會出現，略過

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：開站 → 開登入表單 → 登入"""
        self.goto()
        self.open_login_form()
        self.login(username, password)
