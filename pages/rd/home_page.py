"""
首頁 Page Object — rd 站點 (狗狗娛樂城)
登入成功後的首頁驗證與登出

⚠️ RD 與 rc/re 的差異：
- RD navbar **不顯示 username/avatar**（藏在「個人資訊」menu 內，要點開才出現）
- 因此 verify_login_success 不能用 `text={username}`，改用「登錄」按鈕消失當信號
- is_logged_in / verify_logged_in 同樣用「登錄按鈕消失」判定
"""

from playwright.sync_api import Page, expect
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present, wait_loading_if_present
from utils.screenshot_helper import get_screenshotter


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # Selectors
        # navbar 「登錄」按鈕（未登入才出現），用 button.neon-btn 過濾掉 modal/下載 等其他主按鈕
        self.login_btn  = page.locator('button.neon-btn', has_text="登錄")
        # 「個人資訊」是 navbar 永遠存在的 menu icon（不論登入態），用作登入後 navbar 已 hydrate 的信號
        self.personal_info_menu = page.locator('text=個人資訊').first
        # 登出按鈕：點「個人資訊」進 dropdown / page 後才出現（待後續 probe）
        self.logout_btn = page.locator('button', has_text="登出")
        # 為了 logout flow API 一致，留 avatar 介面但 RD 上實際是「個人資訊」icon
        self.avatar = self.personal_info_menu

    def is_logged_in(self) -> bool:
        """判斷目前是否已登入（navbar 「登錄」按鈕消失即代表）"""
        try:
            return not self.login_btn.is_visible(timeout=3000)
        except Exception:
            return False

    def verify_logged_in(self):
        """輕量驗證：已登入（「登錄」按鈕消失即代表）。無副作用。
        對齊 rc/re/lt 的 API；RD 因 navbar 不顯示 avatar，改以「登錄」消失判定。
        """
        sh = get_screenshotter(self.page)
        expect(self.login_btn).not_to_be_visible(timeout=10000)
        if sh: sh.capture(self.personal_info_menu, "verify_已登入_navbar")

    def verify_login_success(self, username: str):
        """驗證登入成功：navbar「登錄」按鈕消失。

        RD 與 rc/re 不同：navbar 不顯示帳號名（藏在「個人資訊」menu 內），
        也無 visible avatar，無法用 text={username} 或 avatar 驗證。
        最可靠的信號是「登錄」按鈕消失（登入後 navbar UI 重新 render）。
        username 參數保留以對齊 API，實際用作 screenshot label。
        """
        sh = get_screenshotter(self.page)
        expect(self.login_btn).not_to_be_visible(timeout=10000)
        if sh: sh.full_page(f"verify_登入成功_{username}")

    def dismiss_any_popups(self):
        """進首頁後清除可能出現的彈窗（伺服器錯誤 / 公告）"""
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
        """點擊主導覽列項目（真人 / 電子 / 捕魚 / 體育 / 彩票 / 鬥雞）"""
        sh = get_screenshotter(self.page)
        nav = self.page.locator(f"text={name}").first
        nav.scroll_into_view_if_needed()
        if sh: sh.capture(nav, f"click_導覽_{name}")
        nav.click()
        if wait_loading_if_present(self.page):
            if sh: sh.full_page(f"loading_完成_分類_{name}")

    def logout(self):
        """點擊頭像 → 選擇登出 → 驗證登出成功"""
        sh = get_screenshotter(self.page)
        dismiss_server_error_if_present(self.page)
        self.open_user_dropdown()
        dismiss_server_error_if_present(self.page)
        self.logout_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.logout_btn, "click_登出")
        self.logout_btn.click()
        # 驗證登出成功：右上角出現「登錄」按鈕（注意 RD 用「登錄」非「登入」）
        expect(self.login_btn).to_be_visible(timeout=5000)
        if sh: sh.capture(self.login_btn, "verify_登出成功")
