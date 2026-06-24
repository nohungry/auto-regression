"""
KS 後台測試專用 conftest（Super9娛樂城，Vue admin 代理後台）

本檔僅做**代理層級** read-only smoke（同 LU/LG 代理）：
- agent_dashboard_page：以代理帳號 SITE_KS_DASHBOARD_AGENT_USER 登入（無 -admin 入口，無 2FA）
- go_agent_dashboard：每個導航測試前回到落點頁

KS 代理為空帳號（0 會員）→ 不做存提，僅 login + 導航 + logout smoke。
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
    """固定使用 ks 站設定"""
    return get_site_config("ks")


@pytest.fixture(scope="session")
def agent_dashboard_page(browser, site_config):
    """
    Session-scoped 已登入後台 page（代理層級，無 2FA）。
    使用 .env 的 SITE_KS_DASHBOARD_AGENT_URL/USER/PASS（無 -admin 入口）。
    獨立 browser context，避免與前台 cookie 衝突。
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

    # 登入前先掛上 screenshotter，讓登入流程每步都截到圖
    sh = ScreenshotHelper(
        page, "dashboard_agent_login", "KS 後台代理登入（無 2FA）",
        site_id=site_config.site_id, category="feature",
    )
    attach_screenshotter(page, sh)
    try:
        DashboardLoginPage = get_dashboard_login_page_class(site_config.site_id)
        login = DashboardLoginPage(page, site_config.dashboard_agent_url)
        # 代理走代理入口；agent_totp 條件式（KS 代理無 2FA → 自動跳過）
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
