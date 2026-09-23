"""
登入頁面 Page Object — lt 站點（LM來財信用網；2026-09-13 rewrite，第三次換版）

dev-lt 自 2026-07-23 起改用與 RC（王老吉）相同的前台模板，本檔依 2026-09-13 實機
probe 重寫（probe 筆記：dev-notes/lt-redesign-v3-probe-2026-09-13.md）。

新版登入流程：
  /login（獨立路由，非 modal）→ fill 帳密 → click button.primary-btn
    → [用戶協議彈窗] click .dialog-container button.black-btn（fresh context 必現）
    → route 轉回 `/`，DLT cookie 出現代表登入完成

vs 2026-05-18 desktop responsive 版的差異（舊假設全部失效）：
- 帳號/密碼欄改 `input.input-style[type=text|password]`（舊 `input.password-input` 不存在）
- 送出鈕改 `button.primary-btn`（舊 `button.base-btn.type1` 不存在）
- 「先去逛逛」按鈕（舊 `button.base-btn.type2`）已移除，關閉登入頁改按 `img[alt="Exit"]`
- 首頁登入入口改 navbar `button.nav-login-btn`（舊底部 tabbar `.footer-bg .content` 已移除）
- 用戶協議確定鈕改 `button.black-btn`（舊 `.dialog-mask-full div[cursor-pointer]`）
- 一般 click 即可觸發（舊版 Vue handler 需 dispatch_event 的問題不再出現）
- 首頁有 RC 型進站公告 `.popup-announcement-mask`，不清會全屏攔截點擊

不變：錯誤提示彈窗仍是 `button.toast-confirm-btn`（密碼錯誤 / 帳號不存在），
登入完成標記仍是 DLT cookie。
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.dialog_helper import (
    dismiss_announcement_popup_if_present,
    dismiss_server_error_if_present,
)
from utils.screenshot_helper import get_screenshotter
from utils.locale_helper import set_locale


class LoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.login_url = base_url.rstrip("/") + "/login"

        # /login 表單（locale-agnostic：走 class + type，不綁 placeholder 文案）
        self.username_input = page.locator("input.input-style[type='text']").first
        self.password_input = page.locator("input.input-style[type='password']").first
        self.login_btn = page.locator("button.primary-btn").first
        # 登入頁右上角離開鍵（回首頁）
        self.exit_btn = page.locator("img[alt='Exit']").first

        # 首頁 navbar 登入 CTA（未登入才存在）
        self.login_trigger_btn = page.locator("button.nav-login-btn").first

        # 用戶協議彈窗：確定 / 取消（結構性定位，不綁文案）
        self.ua_confirm_btn = page.locator(".dialog-container button.black-btn").first
        self.ua_cancel_btn = page.locator(".dialog-container button.dialog-cancel-btn").first

        # 錯誤提示彈窗確定鈕（密碼錯誤 / 帳號不存在）
        self.error_confirm_btn = page.locator("button.toast-confirm-btn").first

    # ── 導覽 ────────────────────────────────────────────────

    def goto(self, locale: str = "tw"):
        """開啟首頁（預設語系 cookie）並清進站公告。

        Nuxt SPA 的 `load` event 偶爾 30s 內不觸發 → 用 domcontentloaded 再 best-effort
        等 networkidle（讓 lazy 圖片 settle），逾時不視為錯誤。
        """
        set_locale(self.page, self.base_url, locale)
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=12000)
        except PlaywrightTimeoutError:
            pass
        dismiss_server_error_if_present(self.page)
        dismiss_announcement_popup_if_present(self.page)

    def goto_login(self, locale: str = "tw"):
        """直接導向 /login（獨立路由）並等表單可見。"""
        set_locale(self.page, self.base_url, locale)
        self.page.goto(self.login_url, wait_until="domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=12000)
        except PlaywrightTimeoutError:
            pass
        self.username_input.wait_for(state="visible", timeout=15000)

    def open_login_form(self):
        """從首頁點 navbar「登入」CTA 進入 /login。

        與 RC 同型的 hydration dead zone 對策：button 早於 click handler 進 DOM，
        太早點會靜默無效 → click → 短等表單 → 沒出現就再點，最多 10 次（≈15s）。
        點擊前先清進站公告，否則 `.popup-announcement-mask` 會攔截 pointer events。

        與 RC 的關鍵差異：RC 登入是**同頁 modal**（button 點完仍在 DOM，可無腦重點），
        LT 是**route 導航**到 /login，導航一發生 button 就從 DOM 消失。因此每輪重點前
        先檢查是否已離開首頁，且 click 自帶短 timeout —— 否則導航一慢過短等窗口，
        下一輪就會對已消失的 button auto-wait 到預設 30s 才拋錯。
        """
        sh = get_screenshotter(self.page)
        dismiss_announcement_popup_if_present(self.page)
        self.login_trigger_btn.wait_for(state="visible", timeout=15000)
        self.login_trigger_btn.scroll_into_view_if_needed()

        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            # 導航已發生 → CTA 已不在 DOM，再點只會空等；交給迴圈外的表單等待收尾
            if "/login" in self.page.url:
                break
            if sh and (attempt == 1 or attempt == max_attempts):
                label = "click_登入CTA" if attempt == 1 else f"click_登入CTA_attempt{attempt}"
                sh.capture(self.login_trigger_btn, label)
            try:
                self.login_trigger_btn.click(timeout=5000)
            except PlaywrightTimeoutError:
                # CTA 隨導航消失（慢導航），不是失敗；由下方表單等待判定結果
                break
            try:
                self.username_input.wait_for(state="visible", timeout=1500)
                if sh and attempt > 1:
                    sh.capture(self.username_input, f"verify_登入表單_開啟於attempt{attempt}")
                return
            except PlaywrightTimeoutError:
                continue
        # 仍未開啟 → 讓最後一次等待拋出完整 timeout 訊息供 debug
        self.username_input.wait_for(state="visible", timeout=10000)

    # ── 登入 ────────────────────────────────────────────────

    def login(self, username: str, password: str, expect_success: bool = True):
        """填帳密 → 送出 → 處理用戶協議彈窗。

        expect_success=True（預設）：送出後守衛「已離開 /login」，確保回到首頁才回傳。
        負向測試（錯誤憑證 / 空欄位）必須傳 False —— 那些情境本來就會留在 /login，
        帶守衛會被 timeout 誤傷。
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

        # 用戶協議彈窗（fresh context 必現；錯誤路徑不會出現，短等即略過）
        self._handle_user_agreement()

        if expect_success:
            self.page.wait_for_url(lambda url: "/login" not in url, timeout=20000)
            try:
                self.page.wait_for_load_state("networkidle", timeout=12000)
            except PlaywrightTimeoutError:
                pass
            dismiss_server_error_if_present(self.page)
            dismiss_announcement_popup_if_present(self.page)
            if sh: sh.full_page("verify_登入完成_已離開登入頁")

    def _handle_user_agreement(self, timeout: int = 8000):
        """若用戶協議彈窗出現則按確定；沒出現（非首次或錯誤路徑）直接略過。"""
        sh = get_screenshotter(self.page)
        try:
            self.ua_confirm_btn.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            return
        if sh: sh.capture(self.ua_confirm_btn, "click_用戶協議_確定")
        self.ua_confirm_btn.click()
        try:
            self.ua_confirm_btn.wait_for(state="hidden", timeout=5000)
        except PlaywrightTimeoutError:
            pass

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：直接開 /login → 登入。"""
        self.goto_login()
        self.login(username, password)
