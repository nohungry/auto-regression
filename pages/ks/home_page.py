"""
首頁 Page Object — ks 站點（Super9娛樂城）
登入成功後的首頁驗證、彈窗清理、登出

probe 結果（selector-explorer 2026-06-05；KS 與 LG 同框架但組件細節不同）：
- 無 .balance-color → 已登入信號用 nav wallet 圖示（.nav-bg img[alt='Wallet']）；
  KS 有顯示 username，故 verify_login_success 仍用 .nav-bg to_contain_text(username)
- 無 avatar dropdown：點 hamburger（.nav-bg .hidden.h-[34px].w-[32px].cursor-pointer）
  展開右側 drawer（div.fixed.right-0.top-[50px]）；登出是真 button.secondary-btn
- 進站公告單層（.dialog-container.w-full + .close-wrap）
- nav 分類 ul.nav-item li（KS 有 7 項）
- Tailwind arbitrary-value class 方括號在 selector 內需跳脫（Python 字串為 \\[ \\]）
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # 已登入信號：nav wallet 圖示（登入後才渲染）
        self.wallet_indicator = page.locator(".nav-bg img[alt='Wallet']").first
        # nav 容器（驗證帳號顯示）
        self.nav_bar = page.locator(".nav-bg")

        # 未登入信號：nav 登入 CTA
        self.login_cta = page.locator("button.gold-btn").first

        # hamburger（展開右側 drawer，登出入口）；hidden class 在 desktop 為 lg:block
        self.menu_trigger = page.locator(
            ".nav-bg .hidden.h-\\[34px\\].w-\\[32px\\].cursor-pointer"
        ).first
        # 右側 drawer
        self.drawer = page.locator(".fixed.right-0.top-\\[50px\\]").first
        # 登出 button（drawer 內，真 button，可直接 click）
        self.logout_btn = page.locator(
            ".fixed.right-0.top-\\[50px\\] button.secondary-btn"
        ).first

        # 進站公告關閉。用 max-w-[840px] 精準鎖定公告（登入 modal 也含 w-full + close-wrap，避免命中 2 個）
        self.announce_close = page.locator(
            ".dialog-container.max-w-\\[840px\\] .close-wrap"
        )

    # ------------------------------------------------------------------
    # 登入狀態驗證
    # ------------------------------------------------------------------

    def is_logged_in(self) -> bool:
        """判斷目前是否已登入（wallet 圖示可見）"""
        try:
            return self.wallet_indicator.is_visible(timeout=3000)
        except Exception:
            return False

    def verify_logged_in(self):
        """輕量驗證：nav wallet 圖示可見即代表已登入。"""
        sh = get_screenshotter(self.page)
        expect(self.wallet_indicator).to_be_visible(timeout=10000)
        self.wallet_indicator.scroll_into_view_if_needed()
        if sh: sh.capture(self.wallet_indicator, "verify_已登入_wallet圖示")

    def verify_login_success(self, username: str):
        """驗證登入成功：wallet 圖示可見 + nav 區塊文字含登入帳號。

        斷言策略：
        - .nav-bg img[alt='Wallet'] 可見（登入後才渲染）
        - .nav-bg 整體文字含 username（KS 有顯示帳號）
        """
        sh = get_screenshotter(self.page)

        expect(self.wallet_indicator).to_be_visible(timeout=15000)
        self.wallet_indicator.scroll_into_view_if_needed()
        if sh: sh.capture(self.wallet_indicator, "verify_wallet圖示")

        if sh: sh.capture(self.nav_bar, f"verify_帳號顯示_{username}")
        expect(self.nav_bar).to_contain_text(username, timeout=5000)

    def verify_logged_out(self):
        """驗證已登出：首頁登入 CTA 重新出現。"""
        sh = get_screenshotter(self.page)
        expect(self.login_cta).to_be_visible(timeout=10000)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "verify_已登出_登入按鈕出現")

    # ------------------------------------------------------------------
    # 彈窗清理
    # ------------------------------------------------------------------

    def dismiss_any_popups(self):
        """關閉進站公告彈窗（單層）。dev 環境 mask transition 卡住，故不等 hidden。"""
        try:
            self.announce_close.wait_for(state="visible", timeout=1500)
            self.announce_close.dispatch_event("click")
        except PlaywrightTimeoutError:
            pass

    # ------------------------------------------------------------------
    # 導覽
    # ------------------------------------------------------------------

    def click_nav_item(self, category_path: str):
        """點擊頂部 nav 分類連結（ul.nav-item li a[href='/Categories/<x>']）導航。

        KS nav 為 `ul.nav-item li` 內含 `<a href>`；用 dispatch_event 直觸 DOM click，
        繞過 fresh 載入 ~12s 才出現的進站公告 mask（避免 pointer 攔截）。
        category_path 傳完整 pathname，如 "/Categories/slots"。
        """
        sh = get_screenshotter(self.page)
        if sh: sh.full_page(f"before_click_{category_path.rsplit('/', 1)[-1]}")
        self.page.locator(
            f"ul.nav-item li a[href='{category_path}']"
        ).first.dispatch_event("click")

    # ------------------------------------------------------------------
    # 登出
    # ------------------------------------------------------------------

    def logout(self):
        """登出：點 hamburger 展開右側 drawer → click 登出 button → 驗證登出。

        KS 登出在右側 drawer（無 avatar dropdown）。hamburger 在 desktop 為 lg:block，
        用 dispatch_event 觸發避開可能的 overlay 攔截；登出按鈕是真 button 可直接 click。
        """
        sh = get_screenshotter(self.page)

        self.dismiss_any_popups()

        # 展開 drawer
        if sh: sh.capture(self.menu_trigger, "click_展開drawer")
        self.menu_trigger.dispatch_event("click")

        # 等登出 button 可見（drawer 展開後）
        expect(self.logout_btn).to_be_visible(timeout=5000)
        if sh: sh.capture(self.logout_btn, "verify_drawer_opened")

        # 點登出
        if sh: sh.capture(self.logout_btn, "click_登出")
        self.logout_btn.click()

        # 驗證登出成功：登入 CTA 重現
        expect(self.login_cta).to_be_visible(timeout=10000)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "verify_登出成功")
