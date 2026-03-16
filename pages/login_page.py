"""
登入頁面 Page Object
Selector 來源：Chrome DevTools MCP 探索 dev-drc.t9platform-ph.com
"""

from playwright.sync_api import Page, expect
from utils.dialog_helper import dismiss_server_error_if_present


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
        """開啟首頁，並處理進站伺服器錯誤彈窗"""
        self.page.goto(self.base_url)
        self.page.wait_for_load_state("networkidle")
        dismiss_server_error_if_present(self.page)

    def open_login_form(self):
        """點擊右上角「登入」按鈕開啟登入表單"""
        self.login_trigger_btn.click()
        self.username_input.wait_for(state="visible", timeout=5000)

    def login(self, username: str, password: str):
        """填入帳號密碼並登入"""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_btn.click()

        # 登入後可能出現伺服器錯誤彈窗
        dismiss_server_error_if_present(self.page)

        # 處理「用戶協議」彈窗（首次登入才會出現）
        self._handle_user_agreement()

    def _handle_user_agreement(self):
        """處理用戶協議彈窗（若出現則點確定）"""
        try:
            agreement_btn = self.page.locator("button", has_text="確定")
            agreement_btn.wait_for(state="visible", timeout=3000)
            agreement_btn.click()
        except Exception:
            pass  # 非首次登入不會出現，略過

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：開站 → 開登入表單 → 登入"""
        self.goto()
        self.open_login_form()
        self.login(username, password)
