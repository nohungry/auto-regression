"""
首頁 Page Object — lt 站點（WAP 版，2026-04-21 rewrite）

WAP 改版後沿用的設計：
- 無 hamburger / 桌機 drawer — 會員入口改為底部 tabbar「個人」→ `/member-center` 頁面
- Navbar：`.bg-navbar` 65px sticky，內含 logo、餘額（`p.text-amount`）、登入狀態 pill
- 登入狀態 pill：`p.text-text-light-main`
  - 未登入：顯示 `Not Login` (英) / `尚未登入` (繁) — 隨 locale
  - 已登入：顯示 username
- 底部 tabbar：`.shadow-menubar` fixed bottom，5 個 `div.cursor-pointer` tab
  (維護 / 公告 / [中間 CTA] / 排行榜 / 個人)
- 登出：在 `/member-center` 內的 `button.bg-secondary:has-text("登出")`
"""

import re

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from utils.screenshot_helper import get_screenshotter


# 未登入狀態下登入 pill 可能出現的文字（各語系）— 用於 is_logged_in() 判斷
_NOT_LOGGED_IN_TEXTS = {"Not Login", "尚未登入", "未登录", "未登入"}


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # Navbar selectors
        self.navbar          = page.locator('.bg-navbar').first
        self.navbar_balance  = page.locator('.bg-navbar p.text-amount').first
        # 登入狀態指示 pill（未登入 "Not Login" / 已登入 username）
        self.navbar_login_pill = page.locator('.bg-navbar p.text-text-light-main').first

        # Bottom tabbar：以含 `w-[84px]` 的 cursor-pointer div 為準，避開中間的特殊 CTA
        self.bottom_tab_member = page.locator('.shadow-menubar .cursor-pointer', has_text="個人").first

        # Member center page (/member-center) — 登出按鈕
        self.logout_btn = page.locator('button.bg-secondary', has_text="登出").first
        # Member center 關閉按鈕（右上 X，回首頁）
        self.member_close_btn = page.locator('.absolute.right-2\\.5.top-2\\.5.cursor-pointer').first

        # 未登入時首頁顯示的登入 CTA（從 probe 實測，未登入首頁可能會有此按鈕；保留相容）
        self.login_btn = page.locator('button.btn-login').first

    def is_logged_in(self) -> bool:
        """navbar login pill 文字不屬於「未登入」清單即為已登入。~3s"""
        try:
            self.navbar_login_pill.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            return False
        text = (self.navbar_login_pill.inner_text() or "").strip()
        return text not in _NOT_LOGGED_IN_TEXTS and text != ""

    def verify_logged_in(self):
        """輕量驗證：已登入（navbar pill 不顯示「未登入」類文字）。~3s，無副作用。"""
        sh = get_screenshotter(self.page)
        self.navbar_login_pill.wait_for(state="visible", timeout=10000)
        text = (self.navbar_login_pill.inner_text() or "").strip()
        assert text not in _NOT_LOGGED_IN_TEXTS and text != "", (
            f"expected logged-in state, got pill text: {text!r}"
        )
        if sh: sh.capture(self.navbar_login_pill, "verify_已登入_navbar_pill")

    def verify_login_success(self, username: str):
        """驗證登入成功：navbar pill 顯示 username。"""
        sh = get_screenshotter(self.page)
        expect(self.navbar_login_pill).to_have_text(username, timeout=10000)
        if sh: sh.capture(self.navbar_login_pill, f"verify_帳號顯示_{username}")

    def dismiss_any_popups(self):
        """lt WAP 站點無伺服器錯誤彈窗。登入流程中的 UA / 成功 dialog 由 LoginPage.login() 處理。"""
        pass

    def open_member_center(self):
        """tap 底部「個人」tab → 導向 `/member-center`。冪等：已在 member-center 則跳過。
        用 dispatch_event("click") 規避右下角「24小時客服」浮動圖示對 pointer events 的攔截。
        """
        sh = get_screenshotter(self.page)
        if "/member-center" in self.page.url:
            return
        self.bottom_tab_member.scroll_into_view_if_needed()
        if sh: sh.capture(self.bottom_tab_member, "click_個人tab")
        self.bottom_tab_member.dispatch_event("click")
        self.page.wait_for_url(lambda url: "/member-center" in url, timeout=8000)
        self.logout_btn.wait_for(state="visible", timeout=5000)

    def logout(self):
        """tap 個人 → tap 登出 → 驗證回到未登入狀態"""
        sh = get_screenshotter(self.page)
        self.open_member_center()
        self.logout_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.logout_btn, "click_登出")
        self.logout_btn.click()
        # 登出後 SPA pushState 回首頁，navbar pill 回到「未登入」文字（locale 可能為 Not Login / 尚未登入 等）
        not_logged_in_re = re.compile("|".join(re.escape(t) for t in _NOT_LOGGED_IN_TEXTS))
        expect(self.navbar_login_pill).to_have_text(not_logged_in_re, timeout=10000)
        if sh: sh.capture(self.navbar_login_pill, "verify_登出成功")

    def click_nav_item(self, name: str):
        """點擊主導覽列項目（WAP：遊戲大廳 / 我的最愛 / 台灣真人 / 國際真人 / 更多）"""
        sh = get_screenshotter(self.page)
        nav = self.page.locator('.cat-btn', has_text=name).first
        nav.scroll_into_view_if_needed()
        if sh: sh.capture(nav, f"click_分類_{name}")
        nav.click()
