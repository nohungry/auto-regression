"""
首頁 Page Object — drc 站點
登入成功後的首頁驗證與登出
"""

from playwright.sync_api import Page, expect
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present, wait_loading_if_present
from utils.screenshot_helper import get_screenshotter


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # Selectors
        self.avatar     = page.locator('img[alt="avatar"]')
        self.logout_btn = page.locator('button', has_text="登出")
        self.login_btn  = page.locator('button', has_text="登入")

    def is_logged_in(self) -> bool:
        """判斷目前是否已登入（avatar 可見）"""
        try:
            return self.avatar.is_visible(timeout=3000)
        except Exception:
            return False

    def verify_login_success(self, username: str):
        """驗證登入成功：右上角應顯示帳號名稱"""
        sh = get_screenshotter(self.page)
        username_el = self.page.locator(f"text={username}")
        expect(username_el).to_be_visible(timeout=10000)
        if sh: sh.capture(username_el, f"verify_帳號顯示_{username}")

    def dismiss_any_popups(self):
        """進首頁後清除可能出現的彈窗（伺服器錯誤 / 老吉公告）"""
        dismiss_server_error_if_present(self.page)
        dismiss_announcement_popup_if_present(self.page)

    def open_user_dropdown(self):
        """點擊頭像，展開下拉選單"""
        sh = get_screenshotter(self.page)
        self.avatar.scroll_into_view_if_needed()
        if sh: sh.capture(self.avatar, "click_頭像開啟選單")
        self.avatar.click()
        self.logout_btn.wait_for(state="visible", timeout=5000)

    def click_nav_item(self, name: str):
        """點擊主導覽列項目（真人 / 電子 / 捕魚 等）"""
        sh = get_screenshotter(self.page)
        nav = self.page.locator(f"text={name}").first
        nav.scroll_into_view_if_needed()
        if sh: sh.capture(nav, f"click_導覽_{name}")
        nav.click()
        # 切換分類頁會觸發 loading 動畫，等待消失後再繼續
        if wait_loading_if_present(self.page):
            if sh: sh.full_page(f"loading_完成_分類_{name}")

    def logout(self):
        """點擊頭像 → 選擇登出 → 驗證登出成功"""
        sh = get_screenshotter(self.page)
        dismiss_server_error_if_present(self.page)
        self.open_user_dropdown()
        # 下拉選單開啟後可能再次出現伺服器錯誤彈窗
        dismiss_server_error_if_present(self.page)
        self.logout_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.logout_btn, "click_登出")
        self.logout_btn.click()
        # 驗證登出成功：右上角出現「登入」按鈕
        expect(self.login_btn).to_be_visible(timeout=5000)
        if sh: sh.capture(self.login_btn, "verify_登出成功")
