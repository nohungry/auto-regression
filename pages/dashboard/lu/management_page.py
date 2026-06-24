"""
後台管理頁 Page Object — LU 站點（Dlu測試站）

範圍：read-only 導航 + logout（不含存提）。同時支援站長與代理兩種帳號層級。

實機 probe 關鍵事實：

站長層級（<LU 站長帳號>，2026-06-12）：
- 側欄容器 class 為 `.sidebar hide`（收合/移出畫面）→ 側欄連結永遠在 viewport 外，
  **必須用 `dispatch_event("click")`**（仿 RC CSS-hidden sidebar 慣例，見 CLAUDE.md）。
- 頂層選單 `.sidebar-nav li.parent-li`（18 項）；父項錨點 `a.memberSpan` 帶 `id`=route
  （如 `id="/member"`）。葉節點 `a[href^='#/...']`（如 `#/member/member-registration`）
  即使側欄收合仍在 DOM，可直接 dispatch 導航 → 用 `navigate(route_substr)`。

代理層級（<LU 代理帳號>，2026-06-15）：
- 側欄可見（class `sidebar`，非 `sidebar hide`）；頂層選單僅 **5 項**
  （/member、/agent、/report、/report-bet-count、/statistical-report）。
- 子選單預設收合，需先點父項展開（`div.collapse` 加 `.show`）；
  **葉節點無 href**（`li > a > div.collapse-li-text`，Vue @click 導航）→ 用 `navigate_agent(parent_id)`。

共用：
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

    def parent_route_ids(self) -> list:
        """回傳頂層選單的 route id 清單（父項 `a.memberSpan` 的 id，如 '/member'）。
        locale-agnostic：id 是 route 不是文案，可穩定比對權限/可見選單。
        """
        self.sidebar.first.wait_for(state="attached", timeout=15000)
        spans = self.page.locator(".sidebar-nav li.parent-li a.memberSpan")
        return [spans.nth(i).get_attribute("id") for i in range(spans.count())]

    def navigate(self, route_substr: str):
        """（站長層級）點側欄葉節點導航到含 route_substr 的頁面。
        側欄 .sidebar.hide 收合 → 連結在 viewport 外，必須 dispatch_event("click")。
        站長葉節點為 `a[href^='#/...']`（即使收合仍在 DOM）。
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

    def navigate_agent(self, parent_id: str, leaf_index: int = 0):
        """（代理層級）展開父選單 → 點葉節點導航。回傳導航後 URL。

        代理側欄與站長不同（2026-06-15 probe）：
        - 側欄可見（class `sidebar`，非 `sidebar hide`）。
        - 子選單預設收合，需先點父項 `a.memberSpan[id=parent_id]`（如 `/member`）展開
          （展開後 `div.collapse` 加上 `.show`）。
        - **葉節點無 href**（Vue @click 程式化導航），故用結構定位
          `li.parent-li:has(a.memberSpan[id=parent_id]) div.collapse a`，
          不能沿用站長的 `a[href*=...]`。

        導航判定：URL 含父項 route 段（parent_id）+ 內容容器可見（結構性，不綁文案）。
        """
        sh = get_screenshotter(self.page)
        parent = self.page.locator(f"a.memberSpan[id='{parent_id}']").first
        parent.wait_for(state="attached", timeout=10000)
        parent.dispatch_event("click")  # 展開子選單

        leaf = self.page.locator(
            f"li.parent-li:has(a.memberSpan[id='{parent_id}']) div.collapse a"
        ).nth(leaf_index)
        leaf.wait_for(state="attached", timeout=10000)
        leaf.dispatch_event("click")

        # parent_id 形如 '/member'；導航後 URL hash 應含該段
        self.page.wait_for_url(f"**{parent_id}/**", timeout=15000)
        self.content.first.wait_for(state="visible", timeout=15000)
        if sh:
            sh.full_page(f"verify_代理導航_{parent_id.strip('/').replace('/', '_')}")
        return self.page.url

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
