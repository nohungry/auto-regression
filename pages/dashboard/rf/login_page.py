"""
後台登入頁面 Page Object — RF 站點（金爺娛樂城，信用版）

RF 後台架構（實機 probe 2026-06-17）：
- 登入頁 URL 導向 `#/login`，表單為無 class/id 的 input
  （帳號 `input[type=text]`、密碼 `input[type=password]`）+「登入」button
- **站長與代理皆無 2FA**（不同於 LU 站站長有 TOTP）
- 登入後落點：`#/management/all-management`（站長與代理相同）
- 登入成功信號：`.sidebar-nav` first attached（站長/代理共用）

URL 差異：
- 站長入口：SITE_RF_DASHBOARD_URL（含 -admin）
- 代理入口：SITE_RF_DASHBOARD_AGENT_URL（無 -admin）
"""

from playwright.sync_api import Page
from utils.screenshot_helper import get_screenshotter

# 登入 → 後台落地頁側欄渲染的等待上限。理由同 pages/dashboard/lu/login_page.py：
# 實測現金版後台落地需 7~12s（機器閒置），原 15s 在全量跑時會假性失敗。
LOGIN_LANDING_TIMEOUT = 45000


class DashboardLoginPage:

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

        # 登入表單（input 無 class/id，用 type 區分）
        self.username_input = page.locator("input[type='text']").first
        self.password_input = page.locator("input[type='password']").first
        # RF 後台登入按鈕文案為「登入」（中文），無 type 屬性
        self.login_btn = page.get_by_role("button", name="登入").first

    def goto(self):
        """前往後台登入頁。
        Vue SPA 有長連線（websocket / heartbeat）永遠不會進 networkidle，
        用 domcontentloaded + 表單元素 visible 作為載入完成判斷。
        """
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        self.username_input.wait_for(state="visible", timeout=15000)

    def login(self, username: str, password: str):
        """填入帳號密碼 → 送出。RF 後台無 2FA，不需 TOTP。"""
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

    def verify_login_success(self):
        """驗證登入成功：側欄 `.sidebar-nav` visible（站長/代理共同信號）。

        站長與代理皆落點 `#/management/all-management`；側欄為登入後常駐可見的左選單。
        用 visible（非 attached）避免登入失敗但 DOM 殘留 .sidebar-nav 時誤判成功（假綠燈）。
        """
        sh = get_screenshotter(self.page)
        self.page.locator(".sidebar-nav").first.wait_for(
            state="visible", timeout=LOGIN_LANDING_TIMEOUT
        )
        if sh:
            sh.full_page("verify_後台登入成功")

    def goto_and_login(self, username: str, password: str):
        """完整登入流程：前往登入頁 → 登入 → 驗證成功。
        簽名與 LU DashboardLoginPage.goto_and_login 相容（totp_secret 參數移除）。
        """
        self.goto()
        self.login(username, password)
        self.verify_login_success()
