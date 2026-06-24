"""
RF 後台測試專用 conftest

提供以下 fixture：

session-scoped（read-only smoke 測試用）：
- `dashboard_page`（站長 <RF 站長帳號>）：SITE_RF_DASHBOARD_URL/USER/PASS，**無 2FA**。
  落點 `#/management/all-management`，頂層選單 9 項。
- `agent_dashboard_page`（代理 <RF 代理帳號>）：SITE_RF_DASHBOARD_AGENT_URL/USER/PASS，
  **無 2FA**（站長與代理皆免 TOTP，2026-06-17 probe 確認）。
  落點 `#/management/all-management`，頂層選單 4 項。

function-scoped（state-mutating 測試用）：
- `fresh_dashboard_page`（站長 <RF 站長帳號>，function scope）：
  每個充提測試建立獨立 context，避免 session-scoped page 被 logout smoke 污染。
  測試結束後自動關閉 context。

兩帳號不同（不會互踢 session），同一 pytest session 內可並存。
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
    """固定使用 rf 站設定"""
    return get_site_config("rf")


@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    """
    Session-scoped 已登入後台 page（站長 <RF 站長帳號>，無 2FA）。
    使用 .env 的 SITE_RF_DASHBOARD_URL/USER/PASS（站長入口，含 -admin）。
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

    # 登入前先掛上 screenshotter，讓 login_page 每步（帳號/密碼/成功）都截到圖
    sh = ScreenshotHelper(
        page, "dashboard_login", "RF 後台站長登入（無 2FA）",
        site_id=site_config.site_id, category="feature",
    )
    attach_screenshotter(page, sh)
    try:
        DashboardLoginPage = get_dashboard_login_page_class(site_config.site_id)
        login = DashboardLoginPage(page, site_config.dashboard_url)
        login.goto_and_login(
            site_config.dashboard_user,
            site_config.dashboard_pass,
        )
        sh.generate_report()
    finally:
        detach_screenshotter(page)

    yield page
    context.close()


@pytest.fixture
def go_dashboard(dashboard_page, site_config):
    """導航測試前回到後台管理頁，確保各測試起點一致。
    非 autouse：只有導航測試請求；logout 測試不需要（從任何頁皆可登出）。
    Vue 後台 SPA 有 websocket 長連線，不能用 networkidle。
    RF 站長落點為 `#/management/all-management`。
    """
    dashboard_page.goto(
        f"{site_config.dashboard_url}#/management/all-management",
        wait_until="domcontentloaded",
    )
    dashboard_page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=15000)
    return dashboard_page


@pytest.fixture(scope="session")
def agent_dashboard_page(browser, site_config):
    """
    Session-scoped 已登入後台 page（代理 <RF 代理帳號>，無 2FA）。
    使用 .env 的 SITE_RF_DASHBOARD_AGENT_URL/USER/PASS（代理入口，無 -admin）。
    獨立 browser context；與站長 dashboard_page 不同帳號，互不互踢。
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

    # 登入前先掛上 screenshotter
    sh = ScreenshotHelper(
        page, "dashboard_agent_login", "RF 後台代理登入（無 2FA）",
        site_id=site_config.site_id, category="feature",
    )
    attach_screenshotter(page, sh)
    try:
        DashboardLoginPage = get_dashboard_login_page_class(site_config.site_id)
        login = DashboardLoginPage(page, site_config.dashboard_agent_url)
        login.goto_and_login(
            site_config.dashboard_agent_user,
            site_config.dashboard_agent_pass,
        )
        sh.generate_report()
    finally:
        detach_screenshotter(page)

    yield page
    context.close()


@pytest.fixture
def go_agent_dashboard(agent_dashboard_page, site_config):
    """代理導航測試前回到落點頁（#/management/all-management），確保起點一致。
    RF 代理落點與站長相同（#/management/all-management）。
    """
    agent_dashboard_page.goto(
        f"{site_config.dashboard_agent_url}#/management/all-management",
        wait_until="domcontentloaded",
    )
    agent_dashboard_page.locator(".sidebar-nav").first.wait_for(
        state="attached", timeout=15000
    )
    return agent_dashboard_page


@pytest.fixture
def fresh_dashboard_page(browser, site_config):
    """
    Function-scoped 已登入後台 page（站長 <RF 站長帳號>，無 2FA）。
    供 state-mutating 測試（充提）使用，每次測試建立獨立 browser context，
    避免與 session-scoped dashboard_page 互踢 session、或被 logout smoke 測試污染。
    測試結束後自動關閉 context。
    """
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

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

    sh = ScreenshotHelper(
        page, "topup_login", "RF 後台站長登入（充提測試用）",
        site_id=site_config.site_id, category="feature",
    )
    attach_screenshotter(page, sh)
    try:
        DashboardLoginPage = get_dashboard_login_page_class(site_config.site_id)
        login = DashboardLoginPage(page, site_config.dashboard_url)
        login.goto_and_login(
            site_config.dashboard_user,
            site_config.dashboard_pass,
        )
        sh.generate_report()
    finally:
        detach_screenshotter(page)

    yield page
    context.close()
