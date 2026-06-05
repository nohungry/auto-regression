"""
登入頁面 Page Object — lu 站點（Dlgbet）
框架：Nuxt (Vue)；selector 來源：selector-explorer probe（2026-06-05）

登入流程（modal，非 /auth route，URL 不變）：
  首頁 → 依序關閉雙層進站彈窗（圖片廣告 → 文字公告）→ 點 nav「登錄」CTA
  → 彈出登入 modal → 填帳密 → submit → URL 不變，靠餘額 span 出現 / 登入 CTA 消失判定成功

注意（與姊妹站 LG 差異大，勿照抄 LG）：
- 雙層進站彈窗：圖片廣告（.popup-announcement-mask + button.popup-close-btn）先出現，
  關閉後才出現文字公告（.dialog-container.w-full + .close-wrap）
- 登入 modal 容器是 .dialog-container.max-w-[708px]（LG 是 basis-[388px]）
- input 無 .input-style class，直接用 type 屬性區分
- 登入 modal 內只有 1 個 button（button.main-btn「登錄」），不需 .first
- 錯誤密碼顯示 modal（.dialog-container.mx-auto，max-w-[600px]）而非 toast
- LU 不顯示 username，已登入信號改用 nav 餘額 span
- Tailwind arbitrary-value class 方括號在 selector 內需跳脫（Python 字串為 \\[ \\]）
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/") + "/"

        # nav 右上角「登錄」CTA：neon-btn 是共用 class（登入後另有金色漸層 icon 鈕也是
        # neon-btn），登入 CTA 的識別特徵是灰底 .bg-shade03，登入後即消失。
        self.login_cta = page.locator(
            ".fixed.top-0.z-50 button.neon-btn.bg-shade03"
        ).first

        # 雙層進站彈窗關閉鈕
        self.ad_popup_close = page.locator("button.popup-close-btn")  # 第一層：圖片廣告
        # 第二層：文字公告。用 max-w-[840px] 精準鎖定公告容器——錯誤 modal 容器
        # （.dialog-container.mx-auto.flex.w-full.max-w-[600px]）也含 w-full + .close-wrap，
        # 只用 .w-full 會 strict mode 命中 2 個。
        self.announce_close = page.locator(
            ".dialog-container.max-w-\\[840px\\] .close-wrap"
        )

        # 登入 modal（max-w-[708px] 容器）內帳密 + submit
        self.login_modal = page.locator(".dialog-container.max-w-\\[708px\\]")
        self.username_input = self.login_modal.locator("input[type='text']").first
        self.password_input = self.login_modal.locator("input[type='password']").first
        self.submit_button = self.login_modal.locator("button.main-btn").first

        # 錯誤密碼 modal（max-w-[600px]，mx-auto），非 toast
        self.error_modal = page.locator(".dialog-container.mx-auto").first

    def goto(self):
        """開首頁並等 hydration 完成（nav 登錄 CTA 可見）。

        LU 登入走 modal、URL 不變、首頁背景 polling 不進 networkidle，
        故用 domcontentloaded + 等 CTA 可見。
        """
        # timeout=60s：dev 環境過載時首頁 domcontentloaded 偶爾 >30s（預設值會 fail）；
        # 頁面實際會載入、只是慢，故放寬 navigation timeout，非掩蓋產品問題。
        self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
        self.login_cta.wait_for(state="visible", timeout=15000)

    def dismiss_announcement(self):
        """依序關閉雙層進站彈窗：圖片廣告 → 文字公告。兩者會擋登入 CTA。"""
        # 第一層：圖片廣告彈窗
        try:
            self.ad_popup_close.wait_for(state="visible", timeout=3000)
            self.ad_popup_close.dispatch_event("click")
            self.ad_popup_close.wait_for(state="hidden", timeout=3000)
        except PlaywrightTimeoutError:
            pass
        # 第二層：文字公告彈窗（圖片廣告關掉後才出現）
        try:
            self.announce_close.wait_for(state="visible", timeout=3000)
            self.announce_close.dispatch_event("click")
            self.page.locator(".dialog-container.max-w-\\[840px\\]").first.wait_for(
                state="hidden", timeout=3000
            )
        except PlaywrightTimeoutError:
            pass

    def open_login_modal(self):
        """點 nav 登錄 CTA 開啟登入 modal，等帳號 input 可見。"""
        sh = get_screenshotter(self.page)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "click_開啟登入modal")
        self.login_cta.dispatch_event("click")
        # 20s：dev 過載時登入 modal hydration 偶爾 >10s
        self.username_input.wait_for(state="visible", timeout=20000)

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：開首頁 → 關雙層彈窗 → 開 modal → 填帳密 → 送出。"""
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
        # 用 dispatch_event：dev 變慢時雙層公告彈窗可能延遲渲染、其 .dialog-mask 蓋在
        # submit 鈕上攔截 pointer events（一般 .click() 會 retry 到 timeout）。
        # dispatch_event 直觸 DOM click，繞過 overlay 攔截（CLAUDE.md 既有慣例）。
        self.submit_button.dispatch_event("click")

        if sh: sh.full_page("verify_login_submitted")
