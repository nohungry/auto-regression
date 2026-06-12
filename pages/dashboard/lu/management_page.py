"""
後台管理頁 Page Object — LU 站點（Dlu測試站）

本波範圍：read-only 導航 + logout（不含存提，未來再擴 deposit/withdraw）。

實機 probe（2026-06-12，登入態）關鍵事實：
- 側欄容器 class 為 `.sidebar hide`（收合/移出畫面）→ 側欄連結永遠在 viewport 外，
  **必須用 `dispatch_event("click")`**（仿 RC CSS-hidden sidebar 慣例，見 CLAUDE.md）。
- 頂層選單 `.sidebar-nav li.parent-li`（18 項）；父項錨點 `a.memberSpan` 帶 `id`=route
  （如 `id="/member"`）。葉節點 `a[href^='#/...']`（如 `#/member/member-registration`）
  即使側欄收合仍在 DOM，可直接 dispatch 導航。
- 內容載入信號：`.app-main-content` 容器。
- 右上 `.user-account`（顯示帳號）點擊開下拉選單 → 含 `Reset Password / Wallet /
  Agent Information / Logout`；Logout 為 `a` 文字連結（英文後台；locale 切換時文案會變，
  目前 admin 預設英文，與登入鈕 "Login" 一致採文字定位）。
"""

from playwright.sync_api import Page

from utils.screenshot_helper import get_screenshotter


class ManagementPage:

    def __init__(self, page: Page):
        self.page = page
        self.sidebar = page.locator(".sidebar-nav")
        self.parent_items = page.locator(".sidebar-nav li.parent-li")
        self.content = page.locator(".app-main-content")
        self.user_account = page.locator(".user-account").first
        self.logout_link = page.get_by_role("link", name="Logout")

    def sidebar_item_count(self) -> int:
        """頂層選單（li.parent-li）數量；先等側欄掛上 DOM。"""
        self.sidebar.first.wait_for(state="attached", timeout=15000)
        return self.parent_items.count()

    def navigate(self, route_substr: str):
        """點側欄葉節點導航到含 route_substr 的頁面。
        側欄 .sidebar.hide 收合 → 連結在 viewport 外，必須 dispatch_event("click")。
        以 URL hash 變化 + 內容容器可見作為導航成功判定（結構性，不綁文案）。
        """
        sh = get_screenshotter(self.page)
        link = self.page.locator(f"a[href*='{route_substr}']").first
        link.wait_for(state="attached", timeout=10000)
        link.dispatch_event("click")
        self.page.wait_for_url(f"**{route_substr}**", timeout=15000)
        self.content.first.wait_for(state="visible", timeout=15000)
        if sh:
            sh.full_page(f"verify_導航_{route_substr.replace('/', '_')}")

    def open_user_menu(self):
        """點右上使用者帳號開下拉選單（含 Logout）。"""
        sh = get_screenshotter(self.page)
        self.user_account.click()
        self.logout_link.wait_for(state="visible", timeout=8000)
        if sh:
            sh.capture(self.user_account, "click_使用者選單")

    def logout(self):
        """登出 → 回 #/login（登入表單重現）。"""
        sh = get_screenshotter(self.page)
        self.open_user_menu()
        if sh:
            sh.capture(self.logout_link, "click_登出")
        self.logout_link.click()
        self.page.wait_for_url("**/login**", timeout=15000)
        self.page.locator("input[type='password']").first.wait_for(state="visible", timeout=15000)
        if sh:
            sh.full_page("verify_登出回登入頁")
