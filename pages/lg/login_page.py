"""
登入頁面 Page Object — lg 站點（大撈家娛樂城）
框架：Nuxt (Vue)；selector 來源：selector-explorer probe（2026-06-05）

登入流程（與 QW 不同：LG 是 modal，非 /auth route）：
  首頁 → 先關進站公告彈窗 → 點 nav「登入」CTA → 彈出登入 modal → 填帳密 → submit
  → URL 不變，靠「.balance-color 出現 / 登入 CTA 消失」判定成功

注意：
- /auth 是 Nuxt 404；LG 登入是 modal 彈窗，URL 始終停在首頁 /
- 進站公告彈窗（.dialog-container.w-full，max-w-[840px]）會疊在登入 modal 上方擋點擊，
  必須先 dismiss 才能順利操作登入 CTA / modal
- 登入 modal（.dialog-container.basis-[388px]）含登入/註冊兩個 tab，預設登入 tab
- 兩個 input 的 class 同為 .input-style，placeholder 為中文（locale-sensitive），
  必須用 type 屬性區分帳密
- Tailwind arbitrary-value class（h-[30px]、basis-[388px]）在 CSS selector 中
  方括號需跳脫（Python 字串內為 \\[ \\]）
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/") + "/"

        # nav 右上角「登入」CTA：border-white 無背景（與橘色 .orange-btn 註冊鈕區分）
        # probe 驗證 button.h-[30px].w-[90px] 唯一命中
        self.login_cta = page.locator("button.h-\\[30px\\].w-\\[90px\\]")

        # 進站公告彈窗關閉 X（max-w-[840px] 容器內的 close-wrap）
        self.announce_close = page.locator(".dialog-container.w-full .close-wrap")

        # 登入 modal（basis-[388px] 容器）內帳密 input；class 同為 input-style，靠 type 區分
        self.username_input = page.locator(
            ".dialog-container input[type='text'].input-style"
        ).first
        self.password_input = page.locator(
            ".dialog-container input[type='password'].input-style"
        ).first

        # 登入 submit：modal 內含 3 個 button（登入 submit + 註冊 tab 的取得驗證碼/註冊鈕，
        # 後兩者 disabled）。登入 submit 為 DOM 第一個且未 disabled，用 .first 命中。
        self.submit_button = page.locator(
            ".dialog-container.basis-\\[388px\\] button"
        ).first

        # 錯誤提示 toast（最外層 overlay，class 含 z-[99999]）；用屬性選擇器避免方括號跳脫
        self.error_toast = page.locator('div[class*="z-[99999]"]').first

    def goto(self):
        """開首頁並等 hydration 完成（nav 登入 CTA 可見）。

        LG 登入走 modal、URL 不變，首頁背景 polling 不會進入 networkidle，
        故用 domcontentloaded + 等 CTA 可見，後續再靠 expect 處理 hydration。
        """
        # timeout=60s：dev 過載時首頁 domcontentloaded 偶爾 >30s 預設值（頁面會載入只是慢）
        self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
        self.login_cta.wait_for(state="visible", timeout=15000)

    def dismiss_announcement(self):
        """關閉進站公告彈窗（若存在）。公告 mask 會擋登入 CTA，登入前必先關。"""
        try:
            self.announce_close.wait_for(state="visible", timeout=3000)
            self.announce_close.dispatch_event("click")
            # 等 mask 收掉（公告容器消失），避免殘留 mask 擋後續點擊
            self.page.locator(".dialog-container.w-full").first.wait_for(
                state="hidden", timeout=3000
            )
        except PlaywrightTimeoutError:
            pass  # 無公告彈窗

    def open_login_modal(self):
        """點 nav 登入 CTA 開啟登入 modal，等帳號 input 可見。

        Nuxt hydration race + dev 過載：CTA 為 SSR 渲染（goto 已等到 visible），
        但 Vue @click handler 可能尚未綁定，dispatch_event 點了無效、modal 不開。
        重試點擊直到 modal input 出現（仿 RD open_login_form）。
        """
        sh = get_screenshotter(self.page)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "click_開啟登入modal")
        for attempt in range(4):
            # CTA 可能被殘留 mask 攔截 pointer events，用 dispatch_event 直觸 DOM
            self.login_cta.dispatch_event("click")
            try:
                self.username_input.wait_for(state="visible", timeout=8000)
                return
            except PlaywrightTimeoutError:
                if attempt == 3:
                    raise
                continue

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：開首頁 → 關公告 → 開 modal → 填帳密 → 送出 → 等成功。"""
        sh = get_screenshotter(self.page)

        self.goto()
        self.dismiss_announcement()
        self.open_login_modal()

        # 填帳號
        self.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.username_input, "fill_username")
        self.username_input.fill(username)

        # 填密碼
        self.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(self.password_input, "fill_password")
        self.password_input.fill(password)

        # 送出（dispatch_event：dev 過載時殘留公告 mask 可能攔截 .click()，直觸 DOM 繞過）
        self.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(self.submit_button, "click_login_submit")
        self.submit_button.dispatch_event("click")

        if sh: sh.full_page("verify_login_submitted")
