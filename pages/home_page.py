"""
首頁 Page Object
登入成功後的首頁驗證與登出
"""

from playwright.sync_api import Page, expect
from utils.dialog_helper import dismiss_server_error_if_present


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # Selectors
        self.avatar     = page.locator('img[alt="avatar"]')
        self.logout_btn = page.locator('button', has_text="登出")
        self.login_btn  = page.locator('button', has_text="登入")

    def verify_login_success(self, username: str):
        """驗證登入成功：右上角應顯示帳號名稱"""
        expect(self.page.locator(f"text={username}")).to_be_visible(timeout=10000)

    def dismiss_any_popups(self):
        """進首頁後清除可能出現的彈窗"""
        dismiss_server_error_if_present(self.page)

    def open_user_dropdown(self):
        """點擊頭像，展開下拉選單"""
        self.avatar.click()
        self.logout_btn.wait_for(state="visible", timeout=5000)

    def logout(self):
        """點擊頭像 → 選擇登出 → 驗證登出成功"""
        dismiss_server_error_if_present(self.page)
        self.open_user_dropdown()
        self.logout_btn.click()
        # 驗證登出成功：右上角出現「登入」按鈕
        expect(self.login_btn).to_be_visible(timeout=5000)
