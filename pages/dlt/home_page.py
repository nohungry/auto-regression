"""
首頁 Page Object — lt 站點
Selector 來源：probe_lt_selectors.py 實機驗證 dev-lt.t9platform.com

與 drc 站主要差異：
- 帳號顯示：[class*="font-medium"] has_text=username（非 text=username，後者不可見）
- 無 img[alt="avatar"]；改用 .hamburger 開啟會員 drawer
- 登出：.hamburger → drawer 內 button:has-text("登出")
- .hamburger 必須用 dispatch_event("click")：drawer overlay（fixed right-0）常駐 DOM，
  即使 drawer 關閉也持續攔截 pointer events，導致一般 click() 永遠 timeout
- drawer 關閉：無法用 Escape 或點擊外側可靠關閉（CSS transform 滑動，非 display:none），
  verify_login_success 改用 page.reload() 重置狀態
- 無 .dialog-container / .close-wrap（會員功能用 drawer 模式）
- 無 .coin-wrap-bg（lt 站餘額位置不同）
- 無 .sidebar-item.* CSS 隱藏側邊欄
- 無伺服器錯誤彈窗（toast-confirm-btn）
"""

from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # Selectors（實機驗證確認）
        self.hamburger  = page.locator(".hamburger").first
        self.logout_btn = page.get_by_role("button", name="登出")
        self.login_btn  = page.get_by_role("button", name="登入")

    def is_logged_in(self) -> bool:
        """判斷目前是否已登入（login_btn 不可見 = 已登入）"""
        try:
            return not self.login_btn.is_visible(timeout=3000)
        except Exception:
            return False

    def verify_login_success(self, username: str):
        """驗證登入成功：漢堡選單出現且 drawer 內顯示帳號名稱
        lt 站帳號名稱只顯示在會員 drawer 內，非首頁 navbar。
        """
        sh = get_screenshotter(self.page)
        # 等待漢堡選單出現（login_btn 消失 = 已登入）
        expect(self.hamburger).to_be_visible(timeout=10000)
        if sh: sh.capture(self.hamburger, "verify_漢堡選單出現")
        # 開啟 drawer 驗證帳號名稱（dispatch_event 繞過 overlay 攔截）
        self.hamburger.dispatch_event("click")
        self.logout_btn.wait_for(state="visible", timeout=5000)
        username_el = self.page.locator('[class*="font-medium"]', has_text=username).first
        expect(username_el).to_be_visible(timeout=5000)
        if sh: sh.capture(username_el, f"verify_帳號顯示_{username}")
        # 關閉 drawer：重新載入頁面（drawer 用 CSS transform，無法透過點擊可靠關閉）
        self.page.reload()
        self.page.wait_for_load_state("networkidle")

    def dismiss_any_popups(self):
        """lt 站點無伺服器錯誤彈窗，不需處理"""
        pass

    def open_member_drawer(self):
        """點擊漢堡選單，開啟會員 drawer
        drawer overlay 常駐 DOM（closed 狀態仍攔截 pointer events），改用 dispatch_event
        """
        sh = get_screenshotter(self.page)
        if sh: sh.capture(self.hamburger, "click_漢堡選單")
        self.hamburger.dispatch_event("click")
        self.logout_btn.wait_for(state="visible", timeout=5000)

    def click_nav_item(self, name: str):
        """點擊主導覽列項目（真人 / 電子 / 捕魚 等）"""
        sh = get_screenshotter(self.page)
        nav = self.page.get_by_text(name, exact=True).first
        nav.scroll_into_view_if_needed()
        if sh: sh.capture(nav, f"click_導覽_{name}")
        nav.click()
        if sh: sh.full_page(f"loading_完成_分類_{name}")

    def logout(self):
        """開啟漢堡選單 → 點登出 → 驗證登出成功"""
        sh = get_screenshotter(self.page)
        self.open_member_drawer()
        # drawer 內的登出按鈕在 viewport 外，不能用 click()，改用 dispatch_event
        self.logout_btn.wait_for(state="visible", timeout=5000)
        if sh: sh.capture(self.logout_btn, "click_登出")
        self.logout_btn.dispatch_event("click")
        expect(self.login_btn).to_be_visible(timeout=5000)
        if sh: sh.capture(self.login_btn, "verify_登出成功")
