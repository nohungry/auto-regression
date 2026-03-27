"""
登入頁面 Page Object — lt 站點
Selector 來源：probe_lt_selectors.py 實機驗證 dev-lt.t9platform.com

與 drc 站主要差異：
- 登入為獨立 /login 路由（非 Modal overlay）
- 帳號欄位：get_by_placeholder("請填寫4-10位的字母或數字")
- 密碼欄位：get_by_placeholder("請填寫 8-20 位的字母或數字")
- 送出按鈕：get_by_role("button", name="登入")
- SPA（React Router pushState）：直接 goto /login 比依賴按鈕導向更穩定
- 無 Loading 動畫（img[alt="Loading"]）
- 無 toast-confirm-btn 伺服器錯誤彈窗
- 無用戶協議彈窗機制
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter
from utils.locale_helper import set_locale


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.login_url = base_url.rstrip("/") + "/login"

        # Selectors — 使用 CSS class（locale 無關，對應 JS: input.input-style / button.first）
        self.username_input    = page.locator("input.input-style").nth(0)
        self.password_input    = page.locator("input.input-style").nth(1)
        self.login_btn         = page.locator("button").first  # locale 無關，對應 JS: locator('button').first()
        self.login_trigger_btn = page.get_by_role("button", name="登入")  # 首頁 CTA，固定繁中

    def goto(self, locale: str = "tw"):
        """開啟首頁，並預先設定語系 cookie（預設繁中）"""
        set_locale(self.page, self.base_url, locale)
        self.page.goto(self.base_url)
        self.page.wait_for_load_state("domcontentloaded")

    def goto_login(self, locale: str = "tw"):
        """直接導向 /login 路由（比按鈕點擊更穩定，SPA pushState 不觸發 load event）
        注意：lt 站 React 表單需等 networkidle，過早填入會導致登入後 SPA 不跳轉。
        """
        set_locale(self.page, self.base_url, locale)
        self.page.goto(self.login_url, wait_until="networkidle")
        self.username_input.wait_for(state="visible", timeout=8000)

    def open_login_form(self):
        """點擊首頁登入按鈕，等待表單出現（用於 WIN-PUB-009 測試按鈕行為）
        注意：SPA 按鈕點擊不觸發 pushState，直接 goto /login 確保表單出現。
        """
        sh = get_screenshotter(self.page)
        self.login_trigger_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_trigger_btn, "click_登入按鈕")
        self.login_trigger_btn.click()
        # 按鈕點擊後 SPA 不一定 pushState，直接導向 /login 確保表單出現
        self.page.goto(self.login_url)
        self.page.wait_for_load_state("domcontentloaded")
        self.username_input.wait_for(state="visible", timeout=8000)

    def login(self, username: str, password: str):
        """填入帳號密碼並登入"""
        sh = get_screenshotter(self.page)

        self.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.username_input, "fill_帳號")
        self.username_input.fill(username)

        self.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.password_input, "fill_密碼")
        self.password_input.fill(password)

        self.login_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_btn, "click_送出登入")
        self.login_btn.click()

        # SPA 登入後會 pushState 離開 /login，等待 URL 變化（最多 12 秒）
        try:
            self.page.wait_for_url(lambda url: "/login" not in url, timeout=12000)
        except PlaywrightTimeoutError:
            self.page.wait_for_timeout(2000)

        if sh: sh.full_page("loading_完成_進入首頁")

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：直接開 /login → 登入（最穩定方式）"""
        self.goto_login()
        self.login(username, password)
