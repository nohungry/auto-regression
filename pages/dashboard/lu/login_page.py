"""
後台登入頁面 Page Object — LU 站點（Dlgbet，後台站名「Dlu測試站」）

LU 後台架構與 RC/RE/LT 不同，且為本 repo 第一個含 TOTP 2FA 的後台，
因此獨立實作（不 re-export RC）。實機 probe（2026-06-12）確認流程：

1. 登入頁 URL 導向 `#/login`，表單為無 class/id 的 input
   （帳號 `input[type=text]`、密碼 `input[type=password]`）+「Login」按鈕
2. 點 Login → （站長）彈出 Two-Factor Authentication modal（`.dialog-container`）
3. OTP 為 6 個獨立 `input.otp-box`（maxlength=1），逐格填入；Vue 元件自動推進焦點
4. 點 `.confirm-btn`「Confirm」→ 導向 `#/dashboard/index`，側欄 `.sidebar-nav` 出現

**帳號層級差異（2026-06-15 probe）**：站長（autolu001）有 2FA modal；下級代理
（norauto001 @ 無 -admin 入口）**無 2FA**，登入後直接落在 `#/member/member-management`。
因此 `_fill_totp` 採**條件式**（短 timeout 偵測 modal，沒出現即跳過），`verify_login_success`
以「側欄出現」為共同成功信號（不綁特定落點 URL，站長/代理皆適用）。

TOTP 6 碼由 utils.totp_helper.get_totp_code(secret) 即時產生（pyotp）。
"""

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter
from utils.totp_helper import get_totp_code


class DashboardLoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

        # 登入表單（input 無 class/id，用 type 區分）
        self.username_input = page.locator("input[type='text']").first
        self.password_input = page.locator("input[type='password']").first
        self.login_btn = page.get_by_role("button", name="Login")

        # 2FA modal
        self.otp_dialog = page.locator(".dialog-container")
        self.otp_boxes = page.locator("input.otp-box")
        self.otp_confirm_btn = page.locator("button.confirm-btn", has_text="Confirm")

    def goto(self):
        """前往後台登入頁。
        Vue SPA 有長連線（websocket / heartbeat）永遠不會進 networkidle，
        用 domcontentloaded + 表單元素 visible 作為載入完成判斷。
        """
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        self.username_input.wait_for(state="visible", timeout=15000)

    def login(self, username: str, password: str, totp_secret: str = ""):
        """填入帳號密碼 → 送出 → （站長）處理 2FA TOTP。
        代理層級無 2FA：totp_secret 可不傳，_fill_totp 偵測不到 modal 會自動跳過。
        """
        sh = get_screenshotter(self.page)

        self.username_input.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.username_input, "fill_後台帳號")
        self.username_input.fill(username)

        self.password_input.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.password_input, "fill_後台密碼")
        self.password_input.fill(password)

        if sh:
            sh.capture(self.login_btn, "click_後台登入")
        self.login_btn.click()

        self._fill_totp(totp_secret)

    def _fill_totp(self, totp_secret: str):
        """條件式 2FA：短 timeout 偵測 modal → 有則填 6 碼 Confirm，無則跳過（代理層級）。

        站長登入後會彈 Two-Factor Authentication modal；代理無此步驟。
        不可寫死「一定等 modal」（代理會白等 timeout），故短 timeout 偵測後分流。
        """
        sh = get_screenshotter(self.page)

        # 短 timeout 偵測 2FA modal；沒出現 → 代理層級無 2FA，直接跳過
        try:
            self.otp_dialog.first.wait_for(state="visible", timeout=4000)
        except PlaywrightTimeoutError:
            return

        # 走到這代表有 modal（站長）。沒帶 secret 屬設定錯誤，保險跳過避免噴錯。
        if not totp_secret:
            return

        # modal 出現後才產碼（get_totp_code 含過期緩衝，避免填入途中失效）
        code = get_totp_code(totp_secret)
        n = self.otp_boxes.count()
        for i, digit in enumerate(code):
            if i >= n:
                break
            # 逐格 fill；每格重新 query locator，避免 Vue re-render 後 detached
            self.otp_boxes.nth(i).fill(digit)

        if sh:
            sh.capture(self.otp_dialog.first, "fill_2FA驗證碼")
        self.otp_confirm_btn.first.click()

    def verify_login_success(self):
        """驗證登入成功：側欄 `.sidebar-nav` 出現（站長/代理共同信號）。

        站長落點 `#/dashboard/index`、代理落點 `#/member/member-management`，
        落點 URL 不同，故不綁 URL；側欄渲染是兩者一致的登入成功信號。
        """
        sh = get_screenshotter(self.page)
        self.page.locator(".sidebar-nav").first.wait_for(state="visible", timeout=15000)
        if sh:
            sh.full_page("verify_後台登入成功")

    def goto_and_login(self, username: str, password: str, totp_secret: str = ""):
        """完整登入流程：前往登入頁 → 登入（含 2FA）→ 驗證成功"""
        self.goto()
        self.login(username, password, totp_secret)
        self.verify_login_success()
