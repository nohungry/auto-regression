"""
RC 後台測試專用 conftest
- 固定使用 rc 站設定
- 提供 session-scoped dashboard_page fixture（獨立 browser context）
- 每個測試前回到管理頁

登入帳號來自 .env：
- SITE_RC_DASHBOARD_AGENT_USER/PASS（自動化代理，限定管理/報表權限）
- 若未來需要測試儀表板/公告等需完整權限的功能，改用 SITE_RC_DASHBOARD_USER/PASS（總代）
"""

import pytest
from config.settings import get_site_config
from pages.dashboard.factory import get_dashboard_login_page_class


@pytest.fixture(scope="session")
def site_config():
    """固定使用 rc 站設定"""
    return get_site_config("rc")


@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    """
    Session-scoped 已登入後台 page。
    使用 .env 的 SITE_RC_DASHBOARD_AGENT_USER/PASS（非總代）。
    整個測試 session 只登入一次，所有 dashboard 測試共用。
    獨立 browser context（與前台不共用），避免 cookie 衝突。
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

    # 登入後台（自動化代理帳號，從 .env 讀取）
    DashboardLoginPage = get_dashboard_login_page_class(site_config.site_id)
    login = DashboardLoginPage(page, site_config.dashboard_url)
    login.goto_and_login(
        site_config.dashboard_agent_user,
        site_config.dashboard_agent_pass,
    )

    yield page
    context.close()


@pytest.fixture(autouse=True)
def go_management(dashboard_page, site_config):
    """每個 test 前回到管理頁面。
    Vue 後台 SPA 有 websocket 長連線，不能用 networkidle。
    改用 domcontentloaded + 等主內容區 tab 出現。
    """
    dashboard_page.goto(
        f"{site_config.dashboard_url}#/management/all-management",
        wait_until="domcontentloaded",
    )
    # 等任一 tab-btn 出現（代表 SPA hydration 完成），不依賴數量或順序
    dashboard_page.locator('button.tab-btn').first.wait_for(
        state="attached", timeout=15000
    )
