"""
後台登入頁面 Page Object — LU 站點（Dlgbet，後台站名「Dlu測試站」）

LU 後台架構與 RC/RE/LT 不同，且為本 repo 第一個含 TOTP 2FA 的後台，
因此獨立實作（不 re-export RC）。實機 probe（2026-06-12）確認流程：

1. 登入頁 URL 導向 `#/login`，表單為無 class/id 的 input
   （帳號 `input[type=text]`、密碼 `input[type=password]`）+「Login」按鈕
2. 點 Login → （站長）彈出 Two-Factor Authentication modal（`.dialog-container`）
3. OTP 為 6 個獨立 `input.otp-box`（maxlength=1），逐格填入；Vue 元件自動推進焦點
4. 點 `.confirm-btn`「Confirm」→ 導向 `#/dashboard/index`，側欄 `.sidebar-nav` 出現

**帳號層級差異**：站長（<LU 站長帳號>）有 2FA modal；下級代理（<LU 代理帳號> @ 無 -admin
入口）**2026-06-25 起也強制 2FA**（原本無，站點政策變更）。兩者皆走 OTP modal，落點不同
（站長 `#/dashboard/index`、代理 `#/member/member-management`）。
`_fill_totp` 仍採**條件式**（短 timeout 偵測 modal，沒出現即跳過），故站點未來若再撤 2FA
也不會壞；`verify_login_success` 以「側欄出現」為共同成功信號（不綁落點 URL，兩層級皆適用）。

> 代理首次需「Initial Binding」綁定（伺服器金鑰每次刷新），已於 2026-06-25 完成綁定，
> 金鑰存於 .env `SITE_LU_DASHBOARD_AGENT_TOTP`。

TOTP 6 碼由 utils.totp_helper.get_totp_code(secret) 即時產生（pyotp）。
"""

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter
from utils.totp_helper import get_next_window_totp_code, get_totp_code

# 2FA Confirm → 後台落地頁側欄渲染的等待上限。
# 實測（2026-08-28，CDP、機器閒置）：LU 站長 12.24s / LU 代理 7.34s / QW 站長 7.60s。
# 閒置時就吃掉原本 15s 上限的 82%，全量跑（8 站併發 + 大量截圖寫檔）必然超時
# —— 2026-08-27 全量跑有 18 條後台測試因此假性失敗。故放寬至 45s。
# 這是 session-scoped 登入的一次性等待，放寬不影響整體跑測時間；真失敗（如 2FA 400）
# 仍會在此時限後正常紅燈。
LOGIN_LANDING_TIMEOUT = 45000

# 點 Confirm 後等 `POST /api/TwoFactorAuth/Verify` 回應的上限。
# 攔到 response 才能判定 2FA 成敗（現況：點完 Confirm 不看結果，失敗只表現為
# 後續空等側欄逾時，零可觀測性）。攔不到（逾時）不視為失敗，交還 verify_login_success
# 原路徑判定 —— 前端未來若改走別的 endpoint，測試不會因此假性紅燈。
VERIFY_RESPONSE_TIMEOUT = 15000


def _response_body_snippet(response, limit: int = 200) -> str:
    """取 response body 前 limit 字供錯誤訊息用（含後端 error code，如 AuthenticationFailed）。

    body 可能已被釋放（導頁後）而讀不到 —— 診斷資訊拿不到不該蓋掉原本的失敗訊息，
    故降級成佔位字串而非往外拋。
    """
    try:
        return response.text()[:limit]
    except PlaywrightError as exc:
        return f"<無法讀取 body: {exc}>"


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

    def _submit_totp_code(self, code: str, sh):
        """填入 6 碼 → 點 Confirm → 回傳攔到的 Verify response（攔不到回 None）。

        OTP 元件「填滿自動送出」的假說已於 2026-08-28 實測推翻（填滿 6 格零
        Verify 請求），送出一定要點 Confirm，故可安全地用 expect_response 包住點擊。

        Returns:
            playwright Response（`/TwoFactorAuth/Verify`）；VERIFY_RESPONSE_TIMEOUT
            內沒攔到則回 None（不視為失敗，由呼叫端交還原判定路徑）。
        """
        n = self.otp_boxes.count()
        for i, digit in enumerate(code):
            if i >= n:
                break
            # 逐格 fill；每格重新 query locator，避免 Vue re-render 後 detached
            self.otp_boxes.nth(i).fill(digit)

        if sh:
            sh.capture(self.otp_dialog.first, "fill_2FA驗證碼")

        try:
            with self.page.expect_response(
                lambda r: "/TwoFactorAuth/Verify" in r.url,
                timeout=VERIFY_RESPONSE_TIMEOUT,
            ) as resp_info:
                self.otp_confirm_btn.first.click()
            return resp_info.value
        except PlaywrightTimeoutError:
            return None

    def _fill_totp(self, totp_secret: str):
        """條件式 2FA：短 timeout 偵測 modal → 有則填 6 碼 Confirm，無則跳過（代理層級）。

        站長登入後會彈 Two-Factor Authentication modal；代理無此步驟。
        不可寫死「一定等 modal」（代理會白等 timeout），故短 timeout 偵測後分流。

        送出後判 `POST /api/TwoFactorAuth/Verify` 的 HTTP 結果（D-026）：
        - 攔不到 response → 不重送，交還 `verify_login_success` 原路徑判定。
        - ok → 正常返回。
        - 非 ok（實測為 400 `AuthenticationFailed`，成因是登入頻率 / 產碼到送出的
          過期競態）→ 若 modal 已被前端關閉則無從重送，直接帶第一發證據 fail fast；
          modal 仍在才等下一個 TOTP 窗口取新碼，清空 6 格後重送**恰好一次**。
          同窗口重放必被拒，故一定要跨窗口。
        - 第二發仍非 ok → 截圖 + `RuntimeError` fail fast，**絕不第三次**：續試只會
          加深後端鎖定（規則 2b）。
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
        first_resp = self._submit_totp_code(get_totp_code(totp_secret), sh)

        if first_resp is None or first_resp.ok:
            return

        # 第一發被拒。重送的前提是 modal 還在 —— 前端被拒後常直接退回 `#/login`
        # 並卸載 modal，此時 `.otp-box` 已不存在：硬走重送會先白等一個 TOTP 窗口
        # (~31s)，再因點不到 Confirm 逾時被 _submit_totp_code 吞成 None 而靜默返回，
        # 最後只剩側欄逾時那個沒有診斷資訊的錯誤 —— 正好抵銷本次改動的目的。
        # 故先判 modal 是否仍在，不在就直接帶著第一發的證據 fail fast。
        if not self.otp_dialog.first.is_visible():
            if sh:
                sh.full_page("2FA_Verify_失敗_modal已關閉")
            raise RuntimeError(
                f"2FA Verify 被拒（HTTP {first_resp.status}，"
                f"body：{_response_body_snippet(first_resp)}），"
                "且 2FA modal 已關閉（前端已退回登入頁）故無法重送。"
                "疑似後端 2FA 鎖定 / 登入頻率限制，依 dashboard-technical-notes 規則 2b "
                "停手冷卻 20-30 分鐘再跑，不要繼續重試（會延長鎖定）。"
            )

        # modal 仍在 → 跨窗口取新碼重送一次
        retry_code = get_next_window_totp_code(totp_secret)
        n = self.otp_boxes.count()
        for i in range(n):
            self.otp_boxes.nth(i).fill("")
        second_resp = self._submit_totp_code(retry_code, sh)

        if second_resp is None or second_resp.ok:
            return

        if sh:
            sh.full_page("2FA_Verify_二次失敗")
        raise RuntimeError(
            "2FA Verify 連續兩次失敗（已跨 TOTP 窗口重送一次，不再重試）："
            f"第一次 HTTP {first_resp.status}、第二次 HTTP {second_resp.status}，"
            f"第二次回應 body：{_response_body_snippet(second_resp)}。"
            "疑似後端 2FA 鎖定 / 登入頻率限制，依 dashboard-technical-notes 規則 2b "
            "停手冷卻 20-30 分鐘再跑，不要繼續重試（會延長鎖定）。"
        )

    def verify_login_success(self):
        """驗證登入成功：側欄 `.sidebar-nav` 出現（站長/代理共同信號）。

        站長落點 `#/dashboard/index`、代理落點 `#/member/member-management`，
        落點 URL 不同，故不綁 URL；側欄渲染是兩者一致的登入成功信號。

        逾時（登入失敗，通常已被退回 `#/login`）先補一張全頁截圖再拋 ——
        現況失敗零證據，reviewer 無從判斷停在哪一頁。
        """
        sh = get_screenshotter(self.page)
        try:
            self.page.locator(".sidebar-nav").first.wait_for(
                state="visible", timeout=LOGIN_LANDING_TIMEOUT
            )
        except PlaywrightTimeoutError:
            if sh:
                sh.full_page("verify_後台登入失敗")
            raise
        if sh:
            sh.full_page("verify_後台登入成功")

    def goto_and_login(self, username: str, password: str, totp_secret: str = ""):
        """完整登入流程：前往登入頁 → 登入（含 2FA）→ 驗證成功"""
        self.goto()
        self.login(username, password, totp_secret)
        self.verify_login_success()
