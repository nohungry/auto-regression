"""
登入頁面 Page Object — lt 站點（desktop responsive 版，2026-05-18 rewrite）

LT 登入流程（probe 2026-05-18）：
  fill 帳密 → click button.base-btn "會員登入"（dispatch_event）
    → [UA Dialog] click .dialog-mask-full div[class*='cursor-pointer'] "確定"（dispatch_event；首次登入裝置才出現）
    → DLT cookie 出現代表登入完成

關鍵變動（vs 2026-04-21 WAP 版）：
- 2-step flow（沒有 success dialog）
- viewport 從 iPhone 13 mobile → desktop responsive（在 tests/lt/conftest.py）
- 登入完成判斷不能用 URL（Nuxt SPA pushState 後 page.url 仍顯示 /login），改用 DLT cookie
- login button、UA dialog 確定 都需 dispatch_event（Vue handler 攔截 + dialog 是 div 不是 button）
- 錯誤 dialog 確定按鈕：button.toast-confirm-btn（取代舊 button.confirm-btn）
"""

import time

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter
from utils.locale_helper import set_locale


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.login_url = base_url.rstrip("/") + "/login"

        # /login form selectors（locale-agnostic）
        # password input 同時帶 input-style + password-input；用 password-input 精準命中
        self.username_input = page.locator("input.input-style:not(.password-input)").first
        self.password_input = page.locator("input.password-input").first
        # 結構性 locale-agnostic：type1=會員登入、type2=先去逛逛
        # 不用 filter(has_text=...)，文案會隨 locale 變化（cn/en/th/vn）
        self.login_btn = page.locator("button.base-btn.type1").first
        self.browse_btn = page.locator("button.base-btn.type2").first

        # 首頁底部 tabbar「個人」— 未登入時 tap 進 /login
        # 結構性 locale-agnostic：footer 5 個 .content tab，「個人」固定在最後
        self.member_tab = page.locator(".footer-bg .content").last

        # UA dialog 確定按鈕（首次登入裝置會出現使用者協議）
        # 容器是 div 不是 button，必須 dispatch_event 觸發
        self.ua_confirm_btn = (
            page.locator(".dialog-mask-full div[class*='cursor-pointer']")
            .filter(has_text="確定")
            .first
        )

        # 錯誤 dialog 確定按鈕（密碼錯誤 / 帳號不存在）
        self.error_confirm_btn = page.locator("button.toast-confirm-btn").first

    def goto(self, locale: str = "tw"):
        """開啟首頁，並預先設定語系 cookie"""
        set_locale(self.page, self.base_url, locale)
        self.page.goto(self.base_url)
        self.page.wait_for_load_state("domcontentloaded")

    def goto_login(self, locale: str = "tw"):
        """直接導向 /login（Nuxt SPA：hydrate 完前 form 觸發會失效）"""
        set_locale(self.page, self.base_url, locale)
        self.page.goto(self.login_url, wait_until="networkidle")
        self.username_input.wait_for(state="visible", timeout=8000)

    def open_login_form(self):
        """從首頁 tap 底部「個人」tab 進入 /login。
        - dispatch_event("click") 規避客服浮動圖示對 pointer events 的攔截
        - 前後等 networkidle，避免 Nuxt hydrate 未完成 → @click handler 未綁
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
        """填帳密 → click「會員登入」(dispatch_event) → UA dialog 確定 (dispatch_event)。

        登入完成標準：DLT cookie 存在；不能用 page.url（Nuxt pushState 不更新 url 對象）。
        Caller 若需驗證錯誤路徑（wrong password），dialog 仍會跳，不影響 idempotent UA 處理。
        """
        sh = get_screenshotter(self.page)

        self.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.username_input, "fill_帳號")
        self.username_input.fill(username)

        self.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.password_input, "fill_密碼")
        self.password_input.fill(password)

        if sh: sh.capture(self.login_btn, "click_送出登入")
        # Vue handler 攔截：raw .click() 不觸發 submit，需 dispatch_event
        self.login_btn.dispatch_event("click")

        # 處理 UA dialog（首次登入裝置才出現；錯誤路徑下不會出現，直接 skip）
        self._accept_user_agreement_if_present()

        # 等 DLT cookie 出現（最多 10s）；timeout 不 raise，留給 caller 驗證
        self._wait_for_login_cookie(timeout_ms=10000)

        if sh: sh.full_page("loading_完成_登入結束")

    def _accept_user_agreement_if_present(self):
        """若 UA dialog 出現，tap 確定；否則略過"""
        sh = get_screenshotter(self.page)
        try:
            self.ua_confirm_btn.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            return
        if sh: sh.capture(self.ua_confirm_btn, "click_使用者協議_確認")
        self.ua_confirm_btn.dispatch_event("click")
        try:
            self.ua_confirm_btn.wait_for(state="hidden", timeout=3000)
        except PlaywrightTimeoutError:
            pass

    def _wait_for_login_cookie(self, timeout_ms: int = 10000) -> bool:
        """polling 等 DLT cookie 出現（登入成功標記）；timeout 回 False，不 raise"""
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            for c in self.page.context.cookies():
                if c.get("name") == "DLT" and c.get("value"):
                    return True
            time.sleep(0.2)
        return False

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：直接開 /login → 登入"""
        self.goto_login()
        self.login(username, password)
