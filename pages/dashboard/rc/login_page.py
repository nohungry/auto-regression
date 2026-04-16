"""
後台登入頁面 Page Object — RC 站點
RC 後台不需要 TOTP，純帳密登入。
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


class DashboardLoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

        # Selectors — RC 後台登入表單
        self.username_input = page.locator('input[type="text"]').first
        self.password_input = page.locator('input[type="password"]').first
        self.login_btn = page.locator('button', has_text='登入')

    def goto(self):
        """前往後台登入頁"""
        self.page.goto(self.base_url, wait_until="networkidle")

    def login(self, username: str, password: str):
        """填入帳號密碼並送出登入"""
        sh = get_screenshotter(self.page)

        self.username_input.wait_for(state="visible", timeout=10000)
        self.username_input.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.username_input, "fill_後台帳號")
        self.username_input.fill(username)

        self.password_input.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.password_input, "fill_後台密碼")
        self.password_input.fill(password)

        self.login_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.login_btn, "click_後台登入")
        self.login_btn.click()

    def verify_login_success(self):
        """驗證登入成功：等待 URL 離開登入頁"""
        # 後台登入成功後會導向 #/management 或 #/dashboard
        self.page.wait_for_url("**/management/**", timeout=15000)

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：前往登入頁 → 登入 → 驗證成功"""
        self.goto()
        self.login(username, password)
        self.verify_login_success()
