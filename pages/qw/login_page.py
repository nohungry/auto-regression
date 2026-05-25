"""
登入頁面 Page Object — qw 站點（LM來財娛樂城）
框架：Nuxt (Vue)；selector 來源：Chrome DevTools MCP probe（2026-05-22）

登入流程：
  首頁 → 點「登入」按鈕 → 跳轉 /auth → 填帳密 → submit → 回首頁 /

注意：
- /login 是 Nuxt 404，正確 auth 頁是 /auth
- username/password 的 placeholder 相同，必須用 type 屬性區分
- 多語系站台：selector 全部 CSS-based，不綁文案
- wait_until="networkidle" 保護 Nuxt hydration（與 LT 策略對齊）
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.auth_url = base_url.rstrip("/") + "/auth"

        # /auth 頁面 selectors（locale-agnostic；用 type 屬性區分帳密）
        # 兩個 input 的 placeholder 相同，不可用 placeholder 區分
        self.username_input = page.locator("input.auth-input__field[type='text']")
        self.password_input = page.locator("input.auth-input__field[type='password']")

        # submit 按鈕：用 class 精準命中「立即登入」送出按鈕
        # 注意：button DOM 上沒有 `type` attribute（HTMLButtonElement 預設 type 是 submit
        # 但屬性未寫），所以 [type='submit'] selector 命不中。直接靠 class 組合區分：
        # - 立即登入：.solid-btn-shared.auth-btn
        # - 先去逛逛：.outline-btn-shared.auth-btn（不含 solid）
        self.submit_button = page.locator("button.solid-btn-shared.auth-btn")

    def goto(self):
        """直接導向 /auth（Nuxt：等 networkidle 確保 hydration 完成再 fill）"""
        self.page.goto(self.auth_url, wait_until="networkidle")
        self.username_input.wait_for(state="visible", timeout=10000)

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：導向 /auth → 填帳密 → 送出 → 等跳轉回首頁

        wait_until="networkidle" 策略：
        - QW 為 Nuxt，hydration 前 fill 可能造成 submit 無效（與 LT React SPA 相同症狀）
        - 保守選擇 networkidle；若實跑發現過慢，主 context 可切換為 domcontentloaded + retry
        """
        sh = get_screenshotter(self.page)

        self.goto()

        # 填入帳號
        self.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.username_input, "fill_username")
        self.username_input.fill(username)

        # 填入密碼
        self.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.password_input, "fill_password")
        self.password_input.fill(password)

        # 點擊送出按鈕
        self.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(self.submit_button, "click_login_submit")
        self.submit_button.click()

        # 等待跳轉回首頁（URL 離開 /auth）
        try:
            self.page.wait_for_url(
                lambda url: "/auth" not in url,
                timeout=15000
            )
        except PlaywrightTimeoutError:
            # URL 未離開 /auth：可能登入失敗（錯誤帳密），留給 test 驗證
            pass

        if sh: sh.full_page("verify_login_success")
