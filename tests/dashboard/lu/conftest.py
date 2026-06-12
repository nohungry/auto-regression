"""
LU 後台測試專用 conftest（第一波：login + TOTP 2FA 打通）

- 固定使用 lu 站設定
- 提供 session-scoped dashboard_page fixture（獨立 browser context，視窗最大化）
- 登入使用 .env 的 SITE_LU_DASHBOARD_USER/PASS（站長 autolu001）+ SITE_LU_DASHBOARD_TOTP（2FA）
  （與 RC/RE/LT 用 AGENT 帳號不同：LU 第一波依需求以站長層級驗證登入）

本波尚未做存提（deposit/withdraw），故不提供 go_management 等管理頁 fixture。
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
    """固定使用 lu 站設定"""
    return get_site_config("lu")


@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    """
    Session-scoped 已登入後台 page（含 TOTP 2FA）。
    使用 .env 的 SITE_LU_DASHBOARD_USER/PASS（站長）+ SITE_LU_DASHBOARD_TOTP。
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

    # 登入前先掛上 screenshotter，讓 login_page 每步（帳號/密碼/2FA/成功）都截到圖
    # （session fixture 早於 function-scoped auto_screenshot，否則登入流程會漏截）
    sh = ScreenshotHelper(
        page, "dashboard_login_2fa", "LU 後台登入（含 TOTP 2FA）",
        site_id=site_config.site_id, category="feature",
    )
    attach_screenshotter(page, sh)
    try:
        DashboardLoginPage = get_dashboard_login_page_class(site_config.site_id)
        login = DashboardLoginPage(page, site_config.dashboard_url)
        login.goto_and_login(
            site_config.dashboard_user,
            site_config.dashboard_pass,
            site_config.dashboard_totp,
        )
        sh.generate_report()
    finally:
        detach_screenshotter(page)

    yield page
    context.close()


@pytest.fixture
def go_dashboard(dashboard_page, site_config):
    """導航測試前回到後台儀表板首頁，確保各測試起點一致。
    非 autouse：只有導航測試請求；logout 測試不需要（從任何頁皆可登出）。
    Vue 後台 SPA 有 websocket 長連線，不能用 networkidle。
    """
    dashboard_page.goto(
        f"{site_config.dashboard_url}#/dashboard/index",
        wait_until="domcontentloaded",
    )
    dashboard_page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=15000)
    return dashboard_page
