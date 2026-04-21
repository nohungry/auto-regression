"""
登入頁面 Page Object — lt 站點（WAP 版，2026-04-21 rewrite）

WAP 登入流程（見 dev-notes/lt-wap-audit-2026-04-21.md）：
  btn-login → /api/memberLogin 回 Success 並帶 token
    → [UA Dialog] tap `.ua-btn-text:has-text("確認")`（接受使用者協議）
    → [Success Toast] tap `text=確定`（登入成功提示）
    → SPA pushState 離開 /login，navbar 顯示 username + 餘額

Selector 策略：
- `input.login-input`：locale-agnostic CSS class（×2，nth(0) 為帳號、nth(1) 為密碼）
- `button.btn-login`：locale-agnostic，WAP 送出按鈕（舊 `button.primary-btn` 已失效）
- `button.btn-browse`：未登入瀏覽按鈕（測試暫無使用）
- 首頁不再有獨立「登入」CTA；使用者從底部 tabbar「個人」tap 進入 /login
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter
from utils.locale_helper import set_locale


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.login_url = base_url.rstrip("/") + "/login"

        # Selectors — 全部 locale-agnostic（WAP 版已驗證）
        self.username_input = page.locator("input.login-input").nth(0)
        self.password_input = page.locator("input.login-input").nth(1)
        self.login_btn      = page.locator("button.btn-login")
        self.browse_btn     = page.locator("button.btn-browse")

        # Bottom tabbar「個人」— 從首頁進入 /login 的入口（tap 後 router-push 到 /login）
        self.member_tab = page.locator('.shadow-menubar .cursor-pointer', has_text="個人").first

        # UA dialog 接受按鈕（首次登入要同意使用者協議）
        self.ua_confirm_btn = page.locator('.ua-btn-text', has_text="確認").first
        # 成功提示 dialog 的「確定」按鈕（位於 .dialog-mask 內）
        self.success_dialog_ok_btn = page.locator('.dialog-mask').get_by_text("確定", exact=True).first

    def goto(self, locale: str = "tw"):
        """開啟首頁，並預先設定語系 cookie（預設繁中）"""
        set_locale(self.page, self.base_url, locale)
        self.page.goto(self.base_url)
        self.page.wait_for_load_state("domcontentloaded")

    def goto_login(self, locale: str = "tw"):
        """直接導向 /login 路由（SPA pushState 不觸發 load event，直接 goto 最穩定）
        WAP 版仍為 Nuxt SPA，form 填入前需等 networkidle 確保頁面完成 hydrate。
        """
        set_locale(self.page, self.base_url, locale)
        self.page.goto(self.login_url, wait_until="networkidle")
        self.username_input.wait_for(state="visible", timeout=8000)

    def open_login_form(self):
        """從首頁 tap 底部「個人」tab 進入 /login（取代舊 `get_by_role('button', name='登入')`）。
        WAP 改版後首頁已無獨立登入 CTA，個人 tab 未登入時會導向 /login。
        - 用 dispatch_event("click") 規避右下角「24小時客服」浮動圖示對 pointer events 的攔截
        - dispatch 前後都等 networkidle：避免 Nuxt hydrate 未完成 → @click handler 未綁 → dispatch no-op
        """
        sh = get_screenshotter(self.page)
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        self.member_tab.wait_for(state="visible", timeout=5000)
        if sh: sh.capture(self.member_tab, "click_個人tab進入登入")
        self.member_tab.dispatch_event("click")
        self.page.wait_for_url(lambda url: "/login" in url, timeout=8000)
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        self.username_input.wait_for(state="visible", timeout=10000)

    def login(self, username: str, password: str):
        """填入帳密、送出、處理 UA + 成功 dialog，等 SPA 離開 /login。
        Dialog 處理為 idempotent：若未出現則跳過，不阻塞非 Success 路徑（wrong password）。
        """
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

        # 依序處理 UA dialog → 成功 dialog（任一未出現則 skip）
        self._accept_user_agreement_if_present()
        self._dismiss_success_dialog_if_present()

        # SPA pushState 離開 /login 代表登入完成
        try:
            self.page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
        except PlaywrightTimeoutError:
            # 非 Success 路徑（wrong password / empty fields）會留在 /login，交給 caller 驗證 error
            pass

        if sh: sh.full_page("loading_完成_登入結束")

    def _accept_user_agreement_if_present(self):
        """若 UA dialog 出現，tap 確認；否則略過（非首次登入或已接受過不會出現）"""
        sh = get_screenshotter(self.page)
        try:
            self.ua_confirm_btn.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            return
        if sh: sh.capture(self.ua_confirm_btn, "click_使用者協議_確認")
        self.ua_confirm_btn.click()
        # 等 UA dialog 關閉
        try:
            self.ua_confirm_btn.wait_for(state="hidden", timeout=3000)
        except PlaywrightTimeoutError:
            pass

    def _dismiss_success_dialog_if_present(self):
        """若登入成功提示 dialog 出現，tap 確定；否則略過"""
        sh = get_screenshotter(self.page)
        try:
            self.success_dialog_ok_btn.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            return
        if sh: sh.capture(self.success_dialog_ok_btn, "click_登入成功_確定")
        self.success_dialog_ok_btn.click()
        try:
            self.success_dialog_ok_btn.wait_for(state="hidden", timeout=3000)
        except PlaywrightTimeoutError:
            pass

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：直接開 /login → 登入（最穩定方式）"""
        self.goto_login()
        self.login(username, password)
