"""
後台登入頁面 Page Object — RC 站點（信用版 /management 後台，RC/RE/LT/RD 共用）

RC 後台目前純帳密登入（站長與代理皆無 2FA）。
但保留**條件式 2FA** 機制以防未來啟用：login() 收選用 totp_secret，
僅當有 secret 時才偵測 2FA modal 並填碼，無 secret（現行所有信用版代理）則零延遲跳過。
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter
from utils.totp_helper import get_totp_code


class DashboardLoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

        # Selectors — RC 後台登入表單
        self.username_input = page.locator('input[type="text"]').first
        self.password_input = page.locator('input[type="password"]').first
        self.login_btn = page.locator('button', has_text='登入')

        # 2FA modal（信用版代理目前皆無 2FA；selector 暫沿用 LU Vue admin 已知結構，
        # 待信用版代理實際啟用 2FA 時 probe 校正）
        self.otp_dialog = page.locator('.dialog-container')
        self.otp_boxes = page.locator('input.otp-box')

    def goto(self):
        """前往後台登入頁。
        Vue SPA 有長連線（websocket / heartbeat）永遠不會進 networkidle，
        用 domcontentloaded + 表單元素 visible 作為載入完成判斷。
        """
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        self.username_input.wait_for(state="visible", timeout=15000)

    def login(self, username: str, password: str, totp_secret: str = ""):
        """填入帳號密碼並送出登入，再條件式處理 2FA（如該帳號有設）。"""
        sh = get_screenshotter(self.page)

        # goto() 已等過 visible，這裡避免重複 wait
        self.username_input.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.username_input, "fill_後台帳號")
        self.username_input.fill(username)

        self.password_input.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.password_input, "fill_後台密碼")
        self.password_input.fill(password)

        self.login_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.login_btn, "click_後台登入")
        self.login_btn.click()

        self._maybe_fill_totp(totp_secret)

    def _maybe_fill_totp(self, totp_secret: str):
        """條件式 2FA：僅當提供 totp_secret 時才偵測 modal 並填碼。

        設計（與 LU Vue admin 的條件式 2FA 同精神，但檢查順序最佳化）：
        - **無 secret**（現行所有信用版代理）→ 直接 return，不付偵測延遲。
        - **有 secret 但未跳 modal**（站點端尚未啟用 2FA）→ 寬容跳過。
        - **有 secret 且跳 modal** → get_totp_code 產碼逐格填入 + 點 Confirm/確認。

        ⚠️ 信用版 2FA modal 結構**尚未實機驗證**（目前無啟用 2FA 的信用版代理）；
           OTP selector 暫沿用 LU Vue admin（`.dialog-container` / `input.otp-box`），
           confirm 按鈕用多語寬容比對。待信用版代理實際啟用 2FA 時 probe 校正。
        """
        if not totp_secret:
            return

        try:
            self.otp_dialog.first.wait_for(state="visible", timeout=8000)
        except PlaywrightTimeoutError:
            return  # 有 secret 但站點未跳 2FA modal，寬容跳過

        sh = get_screenshotter(self.page)
        code = get_totp_code(totp_secret)
        n = self.otp_boxes.count()
        for i, digit in enumerate(code):
            if i >= n:
                break
            self.otp_boxes.nth(i).fill(digit)
        if sh:
            sh.capture(self.otp_dialog.first, "fill_2FA驗證碼")

        for name in ("Confirm", "確認", "確定"):
            btn = self.page.locator('button', has_text=name)
            if btn.count():
                btn.first.click()
                break

    def verify_login_success(self):
        """驗證登入成功：等待 URL 離開登入頁"""
        # 後台登入成功後會導向 #/management 或 #/dashboard
        self.page.wait_for_url("**/management/**", timeout=15000)

    def goto_and_login(self, username: str, password: str, totp_secret: str = ""):
        """完整登入流程：前往登入頁 → 登入（含條件式 2FA）→ 驗證成功"""
        self.goto()
        self.login(username, password, totp_secret)
        self.verify_login_success()
