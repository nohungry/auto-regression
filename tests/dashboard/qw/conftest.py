"""
QW 後台測試專用 conftest（LM來財娛樂城，Vue admin 代理後台）

本檔做**代理層級** read-only smoke：
- agent_dashboard_page：以代理帳號 SITE_QW_DASHBOARD_AGENT_USER 登入（無 -admin 入口）
- go_agent_dashboard：每個導航測試前回到落點頁

⚠️ QW 代理**需要 2FA**（與 LU/LG/KS 代理不同）：傳入 SITE_QW_DASHBOARD_AGENT_TOTP，
   LU 的條件式 _fill_totp 會偵測 modal 並填碼。

QW 代理為空帳號（0 會員）→ 不做存提，僅 login + 導航 + logout smoke。
站長層級（-admin + 2FA）本檔暫不涵蓋。
"""

import pytest

from config.settings import get_site_config
from pages.dashboard.factory import get_dashboard_login_page_class
from utils.screenshot_helper import (
    ScreenshotHelper,
    attach_screenshotter,
    detach_screenshotter,
)


@pytest.fixture(scope="session")
def site_config():
    """固定使用 qw 站設定"""
    return get_site_config("qw")


@pytest.fixture(scope="session")
def agent_dashboard_page(browser, site_config):
    """
    Session-scoped 已登入後台 page（代理層級，含 2FA）。
    使用 .env 的 SITE_QW_DASHBOARD_AGENT_URL/USER/PASS/TOTP（無 -admin 入口）。
    獨立 browser context，避免與前台 cookie 衝突。
    整個 session 只登入一次（2FA 帳號避免頻繁登入觸發 rate-limit）。
    """
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    # 視窗最大化（CDP 指令，WSL 連 Windows Chrome 時才會成功；失敗不影響測試）
    try:
        cdp = context.new_cdp_session(page)
        window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
        cdp.send("Browser.setWindowBounds", {
            "windowId": window_id,
            "bounds": {"windowState": "maximized"},
        })
        cdp.detach()
    except Exception:
        pass

    # 登入前先掛上 screenshotter，讓登入流程每步（含 2FA）都截到圖
    sh = ScreenshotHelper(
        page, "dashboard_agent_login", "QW 後台代理登入（含 2FA）",
        site_id=site_config.site_id, category="feature",
    )
    attach_screenshotter(page, sh)
    try:
        DashboardLoginPage = get_dashboard_login_page_class(site_config.site_id)
        login = DashboardLoginPage(page, site_config.dashboard_agent_url)
        # QW 代理需 2FA：傳 agent_totp，條件式 _fill_totp 偵測 modal 後填碼
        login.goto_and_login(
            site_config.dashboard_agent_user,
            site_config.dashboard_agent_pass,
            site_config.dashboard_agent_totp,
        )
        sh.generate_report()
    finally:
        detach_screenshotter(page)

    yield page
    context.close()


@pytest.fixture
def go_agent_dashboard(agent_dashboard_page, site_config):
    """代理導航測試前回到落點頁（#/member/member-management），確保起點一致。"""
    agent_dashboard_page.goto(
        f"{site_config.dashboard_agent_url}#/member/member-management",
        wait_until="domcontentloaded",
    )
    agent_dashboard_page.locator(".sidebar-nav").first.wait_for(
        state="attached", timeout=15000
    )
    return agent_dashboard_page
