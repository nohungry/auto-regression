"""
LT 後台測試專用 conftest
- 固定使用 lt 站設定
- 提供 session-scoped dashboard_page fixture（獨立 browser context）
- 每個測試前回到管理頁

登入帳號：qadlttest1（自動化代理帳號，僅有管理/報表權限，不需 TOTP）
若未來需要測試儀表板/公告等需完整權限的功能，
應使用 .env 中的 dltautotest（總代帳號），另建 conftest。
"""

import pytest
from config.settings import get_site_config
from pages.dashboard.factory import get_dashboard_login_page_class

# 自動化代理帳號（限定權限：管理 + 報表）
# 與 .env 中的 dltautotest（總代）不同，此帳號用於管理頁自動化測試
DASHBOARD_AGENT_USER = "qadlttest1"
DASHBOARD_AGENT_PASS = "Ab123456!"


@pytest.fixture(scope="session")
def site_config():
    """固定使用 lt 站設定"""
    return get_site_config("lt")


@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    """
    Session-scoped 已登入後台 page。
    使用自動化代理帳號 qadlttest1（非總代 dltautotest）。
    整個測試 session 只登入一次，所有 dashboard 測試共用。
    獨立 browser context（與前台不共用），避免 cookie 衝突。
    """
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    # 視窗最大化
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

    # 登入後台（使用自動化代理帳號，不需 TOTP）
    DashboardLoginPage = get_dashboard_login_page_class(site_config.site_id)
    login = DashboardLoginPage(page, site_config.dashboard_url)
    login.goto_and_login(DASHBOARD_AGENT_USER, DASHBOARD_AGENT_PASS)

    yield page
    context.close()


@pytest.fixture(autouse=True)
def go_management(dashboard_page, site_config):
    """每個 test 前回到管理頁面"""
    dashboard_page.goto(
        f"{site_config.dashboard_url}#/management/all-management"
    )
    dashboard_page.wait_for_load_state("networkidle")
