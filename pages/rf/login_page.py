"""
登入頁面 Page Object — rf 站點（金爺娛樂城）
框架：Nuxt (Vue)；selector 來源：實機 probe（dev-rf，2026-06-17）

登入流程（獨立 /Login 路由，非 modal）：
  首頁 → 點 a.btn-login（登入/註冊）→ 導頁至 /Login
  → 填 #desktop-account / #desktop-password → 點 button.login-desktop__submit
  → 依序清 base-modal 確認彈窗（用戶協議*首次 + 登入成功*每次）
  → 進首頁（SITE_RF_URL）

注意：
- 登入入口是 <a>（非 button），class a.btn-login（「登入 / 註冊」文字）
- /Login 頁帳號欄 id='desktop-account'；密碼欄 id='desktop-password'
- 送出 button class = login-desktop__submit
- base-modal 確認鈕 class = btn-gold；取消鈕 class = btn-cancel；
  容器 class = base-modal__container
- 錯誤彈窗也是 base-modal：p.alert-text 顯示錯誤文字
- login() 只送出不清 modal（wrong credential 測試需要看錯誤彈窗）
- complete_login_modals() loop 清 base-modal（最多 4 次）
- goto() 防禦性清 base-modal，處理登入前已有進站公告的情況
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/") + "/"

        # 首頁右上角登入入口（<a> 非 button）
        self.login_entry = page.locator("a.btn-login")

        # /Login 頁表單欄位
        self.username_input = page.locator("#desktop-account")
        self.password_input = page.locator("#desktop-password")

        # 送出按鈕（公開屬性，供測試驗證 form elements exist 時使用）
        self.login_btn = page.locator("button.login-desktop__submit")

        # base-modal 容器（確認彈窗）
        self.modal_container = page.locator(".base-modal__container")

        # modal 確定鈕（btn-gold）
        self.modal_confirm_btn = page.locator(
            ".base-modal__container button.btn-gold"
        )

        # 錯誤提示文字（wrong credential 時出現在 base-modal 內）
        self.alert_text = page.locator("p.alert-text")

    # ------------------------------------------------------------------
    # base-modal 消失偵測（取代硬等，避免關閉動畫 >500ms 的 race）
    # ------------------------------------------------------------------

    # 可見 base-modal 計數：用 offsetParent 判可見（與 conftest observer 同 heuristic），
    # 對 v-if（移出 DOM）與 v-show（display:none）皆準。
    _VISIBLE_MODAL_COUNT_JS = (
        "() => Array.from(document.querySelectorAll('.base-modal__container'))"
        ".filter(e => e.offsetParent !== null).length"
    )

    def _visible_modal_count(self) -> int:
        return self.page.evaluate(self._VISIBLE_MODAL_COUNT_JS)

    def _wait_modal_dismissed(self, prev_visible: int, timeout: int = 3000):
        """等可見 base-modal 數量降到 prev_visible 以下（即剛點的 modal 已關閉）。

        取代「點完硬等 500ms 再重偵測」— 關閉動畫 >500ms 時舊寫法會誤命中同一
        淡出中的 modal。逾時（動畫異常久 / modal 未如期關）不拋，交由外層 loop
        下一輪的 visible 偵測兜底。
        """
        try:
            self.page.wait_for_function(
                "(prev) => Array.from(document.querySelectorAll('.base-modal__container'))"
                ".filter(e => e.offsetParent !== null).length < prev",
                arg=prev_visible,
                timeout=timeout,
            )
        except PlaywrightTimeoutError:
            pass

    # ------------------------------------------------------------------
    # 防禦性清 base-modal（最多 N 次 loop）
    # ------------------------------------------------------------------

    def _dismiss_base_modals(self, max_attempts: int = 4):
        """Loop 清除 .base-modal__container 彈窗（點 btn-gold 確定鈕）。

        每次點完短等 500ms，直到沒有 modal 或達到 max_attempts 上限。
        只點「確定」（btn-gold），不點「取消」（btn-cancel）。
        """
        for _ in range(max_attempts):
            try:
                self.modal_container.first.wait_for(state="visible", timeout=2000)
            except PlaywrightTimeoutError:
                break  # 沒有 modal，結束
            try:
                btn = self.modal_container.locator("button.btn-gold").first
                btn.wait_for(state="visible", timeout=2000)
                btn.scroll_into_view_if_needed()
                n_before = self._visible_modal_count()
                btn.click()
                # 等被點的 modal 真正消失（可見數減少）再重新偵測，取代硬等 500ms
                self._wait_modal_dismissed(n_before)
            except PlaywrightTimeoutError:
                break

    # ------------------------------------------------------------------
    # goto：開首頁
    # ------------------------------------------------------------------

    def goto(self):
        """開首頁（domcontentloaded），並防禦性清除任何已存在的 base-modal。

        timeout=60s：dev 環境過載時首頁 domcontentloaded 偶爾超過預設 30s。
        """
        sh = get_screenshotter(self.page)
        self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
        # 等 a.btn-login 可見，確認 hydration 已完成
        self.login_entry.wait_for(state="visible", timeout=15000)
        # 防禦性清除首頁進站公告（若有 base-modal）
        self._dismiss_base_modals(max_attempts=3)
        if sh:
            sh.full_page("verify_首頁載入完成")

    # ------------------------------------------------------------------
    # open_login_form：點 a.btn-login 導頁到 /Login
    # ------------------------------------------------------------------

    def open_login_form(self):
        """點首頁 a.btn-login，等 /Login 頁 #desktop-account input 可見。

        加一次 retry 吸收 Nuxt hydration race（handler 未綁時點擊無效）。
        """
        sh = get_screenshotter(self.page)
        self.login_entry.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.login_entry, "click_登入入口")
        self.login_entry.click()

        # 等 /Login 頁帳號欄出現
        try:
            self.username_input.wait_for(state="visible", timeout=15000)
        except PlaywrightTimeoutError:
            # 一次重試：再點一次 login entry（若仍在首頁）
            if self.login_entry.is_visible():
                self.login_entry.click()
                self.username_input.wait_for(state="visible", timeout=15000)
            else:
                # 已導頁但 input 還沒出現，再等一次
                self.username_input.wait_for(state="visible", timeout=15000)

        if sh:
            sh.full_page("verify_登入頁載入")

    # ------------------------------------------------------------------
    # login：填表單 + 送出（只送出，不清 modal）
    # ------------------------------------------------------------------

    def login(self, username: str, password: str):
        """填入帳號密碼並送出。不清 base-modal（wrong credential 測試需要看錯誤彈窗）。"""
        sh = get_screenshotter(self.page)

        self.username_input.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.username_input, "fill_帳號欄位")
        self.username_input.fill(username)

        self.password_input.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.password_input, "fill_密碼欄位")
        self.password_input.fill(password)

        self.login_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.login_btn, "click_登入送出")
        self.login_btn.click()

        if sh:
            sh.full_page("verify_登入送出後")

    # ------------------------------------------------------------------
    # complete_login_modals：清正常登入後的 base-modal
    # ------------------------------------------------------------------

    def complete_login_modals(self):
        """Loop 清掉登入成功後的 base-modal（用戶協議 + 登入成功），最多 4 次。

        每次點 .base-modal__container button.btn-gold（確定），不點取消。
        直到沒有 modal 為止。
        """
        sh = get_screenshotter(self.page)
        for attempt in range(4):
            try:
                self.modal_container.first.wait_for(state="visible", timeout=5000)
            except PlaywrightTimeoutError:
                break  # 無 modal，登入流程完成
            btn = self.modal_container.locator("button.btn-gold").first
            try:
                btn.wait_for(state="visible", timeout=3000)
                btn.scroll_into_view_if_needed()
                if sh:
                    sh.capture(btn, f"click_確定彈窗_{attempt + 1}")
                n_before = self._visible_modal_count()
                btn.click()
                # 等被點的 modal 真正消失（可見數減少）再重新偵測，取代硬等 500ms
                self._wait_modal_dismissed(n_before)
            except PlaywrightTimeoutError:
                break

        if sh:
            sh.full_page("verify_登入彈窗清除後")

    # ------------------------------------------------------------------
    # goto_and_login：完整登入流程（供 logged_in_page fixture 呼叫）
    # ------------------------------------------------------------------

    def goto_and_login(self, username: str, password: str):
        """完整登入：開首頁 → 點登入入口 → 填帳密送出 → 清 base-modal → 進首頁。"""
        self.goto()
        self.open_login_form()
        self.login(username, password)
        self.complete_login_modals()
