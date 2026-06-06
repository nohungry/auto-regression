"""
首頁 Page Object — lu 站點（Dlgbet）
登入成功後的首頁驗證、彈窗清理、登出

probe 結果（selector-explorer 2026-06-05；與 LG 結構差異大）：
- LU 不顯示 username（nav/sidebar 皆無帳號名）→ 已登入信號用 nav 餘額 span +
  登入 CTA（button.neon-btn）消失，不可用 to_contain_text(username)
- 無 avatar dropdown：登出功能在左側 sidebar；點 hamburger button.nav-toggle-btn
  展開 sidebar（70px → 270px），登出是真 <button>（收合時 lg:hidden）
- 進站雙層彈窗：圖片廣告（button.popup-close-btn）+ 文字公告（.close-wrap）
- nav 遊戲分類以頁面 card 呈現：a[href*='/Categories/']（6 個）
- Tailwind arbitrary-value class 方括號在 selector 內需跳脫（Python 字串為 \\[ \\]）
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # 已登入信號：nav 餘額數字 span（登入後才渲染）
        self.balance = page.locator(
            ".fixed.top-0.z-50 span.text-xs.font-bold.text-white"
        ).first
        # 未登入信號：nav 登錄 CTA（灰底 .bg-shade03，與登入後金色 icon neon-btn 區分）
        self.login_cta = page.locator(
            ".fixed.top-0.z-50 button.neon-btn.bg-shade03"
        ).first

        # 左側 sidebar 與 hamburger
        self.nav_toggle = page.locator("button.nav-toggle-btn").first
        self.sidebar = page.locator(".fixed.left-0.z-30").first
        # 登出 button（sidebar 展開後唯一 button，class 含 border-shade04）
        self.logout_btn = page.locator(
            ".fixed.left-0.z-30 button[class*='border-shade04']"
        ).first

        # 進站雙層彈窗關閉鈕
        self.ad_popup_close = page.locator("button.popup-close-btn")
        # 用 max-w-[840px] 精準鎖定公告（錯誤 modal 也含 w-full + close-wrap，避免命中 2 個）
        self.announce_close = page.locator(
            ".dialog-container.max-w-\\[840px\\] .close-wrap"
        )

    # ------------------------------------------------------------------
    # 登入狀態驗證
    # ------------------------------------------------------------------

    def is_logged_in(self) -> bool:
        """判斷目前是否已登入（餘額 span 可見）"""
        try:
            return self.balance.is_visible(timeout=3000)
        except Exception:
            return False

    def verify_logged_in(self):
        """輕量驗證：nav 餘額 span 可見即代表已登入。"""
        sh = get_screenshotter(self.page)
        expect(self.balance).to_be_visible(timeout=10000)
        self.balance.scroll_into_view_if_needed()
        if sh: sh.capture(self.balance, "verify_已登入_餘額顯示")

    def verify_login_success(self, username: str):
        """驗證登入成功：nav 餘額 span 可見 + 登錄 CTA 消失。

        斷言策略：
        - 餘額 span 可見（登入後才渲染，明確已登入信號）
        - 登錄 CTA（button.neon-btn）不再可見（nav 由「登錄 註冊」變為「餘額 提現」）
        注意：LU 不顯示 username，故不對 username 字串斷言（與 LG/QW 不同）。
        username 參數僅作 screenshot label 用。
        """
        sh = get_screenshotter(self.page)

        expect(self.balance).to_be_visible(timeout=15000)
        self.balance.scroll_into_view_if_needed()
        if sh: sh.capture(self.balance, f"verify_餘額顯示_{username}")

        expect(self.login_cta).not_to_be_visible(timeout=5000)

    def verify_logged_out(self):
        """驗證已登出：首頁登錄 CTA 重新出現。"""
        sh = get_screenshotter(self.page)
        expect(self.login_cta).to_be_visible(timeout=10000)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "verify_已登出_登錄按鈕出現")

    # ------------------------------------------------------------------
    # 彈窗清理
    # ------------------------------------------------------------------

    def dismiss_any_popups(self):
        """依序關閉進站雙層彈窗（圖片廣告 → 文字公告）。"""
        try:
            self.ad_popup_close.wait_for(state="visible", timeout=1500)
            self.ad_popup_close.dispatch_event("click")
            self.ad_popup_close.wait_for(state="hidden", timeout=2000)
        except PlaywrightTimeoutError:
            pass
        try:
            self.announce_close.wait_for(state="visible", timeout=1500)
            self.announce_close.dispatch_event("click")
            self.page.locator(".dialog-container.max-w-\\[840px\\]").first.wait_for(
                state="hidden", timeout=2000
            )
        except PlaywrightTimeoutError:
            pass

    # ------------------------------------------------------------------
    # 導覽
    # ------------------------------------------------------------------

    def click_nav_item(self, category_path: str):
        """點擊指定遊戲分類連結（a[href='/Categories/<x>']）導航。

        LU nav 為 href-based（無 ul.nav-item）；用 dispatch_event 直觸 DOM click，
        繞過 fresh 載入 ~10s 才出現的進站公告 mask（避免 pointer 攔截）。
        category_path 傳完整 pathname，如 "/Categories/slots"。
        """
        sh = get_screenshotter(self.page)
        if sh: sh.full_page(f"before_click_{category_path.rsplit('/', 1)[-1]}")
        self.page.locator(f"a[href='{category_path}']").first.dispatch_event("click")

    # ------------------------------------------------------------------
    # 登出
    # ------------------------------------------------------------------

    def logout(self):
        """登出：點 hamburger 展開左側 sidebar → click 登出 button → 驗證登出。

        LU 登出在左側 sidebar（無 avatar dropdown）。sidebar 收合時登出 button
        為 lg:hidden，必須先展開。登出後登錄 CTA 重現。
        """
        sh = get_screenshotter(self.page)

        self.dismiss_any_popups()

        # 展開 sidebar
        if sh: sh.capture(self.nav_toggle, "click_展開sidebar")
        self.nav_toggle.dispatch_event("click")

        # 等登出 button 可見（sidebar 展開後才顯示）
        expect(self.logout_btn).to_be_visible(timeout=5000)
        if sh: sh.capture(self.logout_btn, "verify_sidebar_opened")

        # 點登出
        if sh: sh.capture(self.logout_btn, "click_登出")
        self.logout_btn.dispatch_event("click")

        # 驗證登出成功：登錄 CTA 重現
        expect(self.login_cta).to_be_visible(timeout=10000)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "verify_登出成功")
