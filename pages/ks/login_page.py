"""
登入頁面 Page Object — ks 站點（Super9娛樂城）
框架：Nuxt (Vue)；selector 來源：selector-explorer probe（2026-06-05）

KS 與姊妹站 LG 同一套 Nuxt 框架（共用 .nav-bg / .dialog-container / ul.nav-item），
但配色為金色英文主題，多處組件 selector 不同（勿照抄 LG）。

登入流程（modal，非 /auth route，URL 不變）：
  首頁 → 關進站公告（單層）→ 點 nav「Player Login」CTA（button.gold-btn）
  → 彈出登入 modal（.dialog-container.max-w-[388px]）→ 填帳密 → submit（button.primary-btn）
  → URL 不變，靠 wallet 圖示出現 / nav 顯示 username 判定成功

注意：
- 登入 CTA 是 button.gold-btn（共 2 個：Player Login + Free Register，.first 為登入）
- 登入 modal 內有 2 個 button.primary-btn（Login + Register），登入 submit 是 .first
- input 用 .input-style（與 LG 一致）
- 錯誤密碼顯示 modal（div[class*="z-[99999]"]）而非 toast
- KS 有顯示 username（與 LG 一致，LU 則無）
- dev 環境 .dialog-mask 的 fade-leave-active transition 會卡住、mask 不從 DOM 移除，
  故關閉公告後不等 mask hidden（改不阻塞，登入 modal 會疊在上層可正常操作）
- Tailwind arbitrary-value class 方括號在 selector 內需跳脫（Python 字串為 \\[ \\]）
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/") + "/"

        # nav 登入 CTA：button.gold-btn（Player Login + Free Register 同 class，.first 為登入）
        self.login_cta = page.locator("button.gold-btn").first

        # 進站公告彈窗關閉 X（單層）。用 max-w-[840px] 精準鎖定公告容器——登入 modal
        # （.dialog-container.w-full.max-w-[388px]）也含 w-full + .close-wrap，
        # 只用 .w-full 會 strict mode 命中 2 個。
        self.announce_close = page.locator(
            ".dialog-container.max-w-\\[840px\\] .close-wrap"
        )

        # 登入 modal（max-w-[388px] 容器，與公告 max-w-[840px] 區分）
        self.login_modal = page.locator(".dialog-container.max-w-\\[388px\\]")
        self.username_input = page.locator(
            ".dialog-container input[type='text'].input-style"
        ).first
        self.password_input = page.locator(
            ".dialog-container input[type='password'].input-style"
        ).first
        # 登入 submit：modal 內 2 個 primary-btn（Login + Register），登入是 .first
        self.submit_button = page.locator(
            ".dialog-container.max-w-\\[388px\\] button.primary-btn"
        ).first

        # 錯誤密碼 modal（div 含 z-[99999]），非 toast
        self.error_modal = page.locator('div[class*="z-[99999]"]').first

    def goto(self):
        """開首頁並等 hydration 完成（nav 登入 CTA 可見）。"""
        # timeout=60s：dev 過載時首頁 domcontentloaded 偶爾 >30s 預設值（頁面會載入只是慢）
        self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
        self.login_cta.wait_for(state="visible", timeout=15000)

    def dismiss_announcement(self):
        """關閉進站公告彈窗（若存在）。

        dev 環境 mask fade transition 會卡住，故點關閉後不等 mask hidden
        （避免 hang）；登入 modal 會疊在上層，殘留 mask 不影響操作。
        """
        try:
            self.announce_close.wait_for(state="visible", timeout=3000)
            self.announce_close.dispatch_event("click")
        except PlaywrightTimeoutError:
            pass

    def open_login_modal(self):
        """點 nav 登入 CTA 開啟登入 modal，等帳號 input 可見。

        Nuxt hydration race + dev 過載：CTA 為 SSR 渲染（goto 已等到 visible），
        但 Vue @click handler 可能尚未綁定，dispatch_event 點了無效、modal 不開。
        重試點擊直到 modal input 出現（仿 pages/rd/login_page.py open_login_form）。
        """
        sh = get_screenshotter(self.page)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "click_開啟登入modal")
        for attempt in range(4):
            self.login_cta.dispatch_event("click")
            try:
                self.username_input.wait_for(state="visible", timeout=8000)
                return
            except PlaywrightTimeoutError:
                if attempt == 3:
                    raise
                continue

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：開首頁 → 關公告 → 開 modal → 填帳密 → 送出。"""
        sh = get_screenshotter(self.page)

        self.goto()
        self.dismiss_announcement()
        self.open_login_modal()

        self.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.username_input, "fill_username")
        self.username_input.fill(username)

        self.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.password_input, "fill_password")
        self.password_input.fill(password)

        self.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(self.submit_button, "click_login_submit")
        # dispatch_event：KS dev 環境 .dialog-mask fade-leave-active transition 卡住、
        # 公告 mask 不從 DOM 移除，會攔截 submit 的 .click()（timeout）。直觸 DOM click 繞過。
        self.submit_button.dispatch_event("click")

        if sh: sh.full_page("verify_login_submitted")
