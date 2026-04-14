"""
首頁 Page Object — lt 站點
Selector 來源：probe_lt_selectors.py 實機驗證（見 .env SITE_LT_URL）

與 rc 站主要差異：
- 帳號顯示：[class*="font-medium"] has_text=username（非 text=username，後者不可見）
- 無 img[alt="avatar"]；改用 .hamburger 開啟會員 drawer
- 登出：.hamburger → drawer 內 button:has-text("登出")
- .hamburger 必須用 dispatch_event("click")：drawer overlay（fixed right-0）常駐 DOM，
  即使 drawer 關閉也持續攔截 pointer events，導致一般 click() 永遠 timeout
- drawer 關閉：無法用 Escape 或點擊外側可靠關閉（CSS transform 滑動，非 display:none），
  verify_login_success 改用 page.reload() 重置狀態
- 無 .coin-wrap-bg（lt 站餘額位置不同）
- 會員功能以 drawer 為入口，再展開 .dialog-container / .close-wrap 對話框
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
        # Locale-agnostic drawer 開啟信號（img src 不隨語系變動）
        self.drawer_ready_indicator = page.locator('img[src*="betting-details"]')
        # 桌機版 navbar 餘額（mobile 版同 class 但位於 .lg:hidden 容器，w=0）
        # 用 `[class*="lg:flex"]` 屬性包含選到桌機版容器，可避開 drawer 內的 text-amount
        self.navbar_balance = page.locator('div[class*="lg:flex"] p.text-amount').first

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
        self.drawer_ready_indicator.wait_for(state="visible", timeout=5000)
        # 必須 scope 到 drawer 容器：`[class*="font-medium"]` 在 navbar 與 drawer 內都會命中，
        # .first 會抓到 navbar 那條（w=200 的小元素），截圖紅框落點不明顯。
        drawer = self.page.locator('.fixed.bottom-0.right-0')
        username_el = drawer.locator('[class*="font-medium"]', has_text=username).first
        expect(username_el).to_be_visible(timeout=5000)
        if sh: sh.capture(username_el, f"verify_帳號顯示_{username}")
        # 關閉 drawer：重新載入頁面（drawer 用 CSS transform，無法透過點擊可靠關閉）
        self.page.reload()
        self.page.wait_for_load_state("networkidle")

    def dismiss_any_popups(self):
        """lt 站點無伺服器錯誤彈窗，不需處理"""
        pass

    def open_member_drawer(self):
        """點擊漢堡選單，開啟會員 drawer（冪等：drawer 已開啟則跳過點擊）
        drawer overlay 常駐 DOM（closed 狀態仍攔截 pointer events），改用 dispatch_event。
        等待信號改用 img[src*="betting-details"]（locale-agnostic），避免綁死「登出」繁中文案。
        hamburger 是 toggle：若 drawer 已開再次點擊會關閉，故需先判斷狀態。
        開啟判斷：drawer 容器不含 translate-x-full class 即為開啟（is_visible 對 transform 隱藏失效）。
        """
        sh = get_screenshotter(self.page)
        is_open = self.page.evaluate(
            "() => { const c = document.querySelector('.fixed.bottom-0.right-0'); "
            "return c ? !c.className.includes('translate-x-full') : false; }"
        )
        if is_open:
            return
        if sh: sh.capture(self.hamburger, "click_漢堡選單")
        self.hamburger.dispatch_event("click")
        self.drawer_ready_indicator.wait_for(state="visible", timeout=5000)

    def click_nav_item(self, name: str):
        """點擊主導覽列項目（真人 / 電子 / 捕魚 等）"""
        sh = get_screenshotter(self.page)
        nav = self.page.get_by_text(name, exact=True).first
        nav.scroll_into_view_if_needed()
        if sh: sh.capture(nav, f"click_導覽_{name}")
        nav.click()
        if sh: sh.full_page(f"loading_完成_分類_{name}")

    def open_betting_history_dialog(self):
        """開啟會員 drawer → 點選投注紀錄，展開投注紀錄面板"""
        sh = get_screenshotter(self.page)
        self.open_member_drawer()
        betting_icon = self.page.locator('img[alt="投注紀錄"]')
        if sh: sh.capture(betting_icon, "click_投注紀錄入口")
        betting_icon.dispatch_event("click")
        self.page.locator('.dialog-container').wait_for(state="visible", timeout=5000)
        if sh: sh.full_page("verify_投注紀錄面板")

    def open_personal_info_dialog(self):
        """開啟會員 drawer → 點選 Edit 圖示，展開個人資料（會員帳號）面板"""
        sh = get_screenshotter(self.page)
        self.open_member_drawer()
        edit_icon = self.page.locator('img[alt="Edit"]').first
        if sh: sh.capture(edit_icon, "click_個人資料入口")
        edit_icon.dispatch_event("click")
        self.page.locator('.dialog-container').wait_for(state="visible", timeout=5000)
        if sh: sh.full_page("verify_個人資料面板")

    def open_inbox_dialog(self):
        """開啟會員 drawer → 點選會員訊息，展開收件匣面板"""
        sh = get_screenshotter(self.page)
        self.open_member_drawer()
        inbox_icon = self.page.locator('img[alt="會員訊息"]')
        if sh: sh.capture(inbox_icon, "click_收件匣入口")
        inbox_icon.dispatch_event("click")
        self.page.locator('.dialog-container').wait_for(state="visible", timeout=5000)
        if sh: sh.full_page("verify_收件匣面板")

    def open_maintenance_time_dialog(self):
        """開啟會員 drawer → 點選「維護時間」按鈕，展開維護時間對話框
        此按鈕在存款功能開放時顯示「存款」，維護期間顯示「維護時間」。
        dev 站點目前顯示為「維護時間」；以 button[class*='mb-5'] 定位
        （位於登出按鈕上方，具唯一 mb-5 margin），locale-agnostic。
        """
        sh = get_screenshotter(self.page)
        self.open_member_drawer()
        btn = self.page.locator("button[class*='mb-5']").first
        if sh: sh.capture(btn, "click_維護時間入口")
        btn.dispatch_event("click")
        self.page.locator('.dialog-mask').wait_for(state="visible", timeout=5000)
        if sh: sh.full_page("verify_維護時間對話框")

    def close_dialog(self):
        """關閉 dialog-container（點選 close-wrap 關閉圖示）"""
        self.page.locator('.close-wrap img').first.click()

    def close_drawer_if_open(self):
        """若 drawer 處於開啟狀態就點擊 hamburger 關閉（toggle）
        drawer 狀態持久化在 cookie（appLaiTsai.sidebar），reload **不會**關閉——
        唯一可靠關閉方式是再次觸發 hamburger toggle。
        偵測：drawer 容器（.fixed.bottom-0.right-0）不含 translate-x-full 即為開啟。
        （is_visible() 對 transform 隱藏失效——drawer 雖在 viewport 外仍為 visible。）
        """
        is_open = self.page.evaluate(
            "() => { const c = document.querySelector('.fixed.bottom-0.right-0'); "
            "return c ? !c.className.includes('translate-x-full') : false; }"
        )
        if is_open:
            self.hamburger.dispatch_event("click")
            # 等 drawer 容器再度出現 translate-x-full class（動畫可能需要時間）
            self.page.wait_for_function(
                "() => { const c = document.querySelector('.fixed.bottom-0.right-0'); "
                "return c && c.className.includes('translate-x-full'); }",
                timeout=3000,
            )

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
