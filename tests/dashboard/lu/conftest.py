"""
LU 後台測試專用 conftest

提供兩個帳號層級的 session fixture（各自獨立 browser context，視窗最大化）：

- `dashboard_page`（站長 <LU 站長帳號>）：SITE_LU_DASHBOARD_URL/USER/PASS + TOTP（2FA）。
  落點 `#/dashboard/index`，頂層選單 18 項。
- `agent_dashboard_page`（代理 <LU 代理帳號>）：SITE_LU_DASHBOARD_AGENT_URL/USER/PASS，
  **無 2FA**（2026-06-15 probe 確認）。落點 `#/member/member-management`，頂層選單 5 項。

兩帳號不同（不會互踢 session），同一 pytest session 內可並存。
存提（deposit/withdraw）暫不做：代理 <LU 代理帳號> 為空帳號（0 會員 / 0 餘額 / 0 銀行卡），
無法做可逆的對稱 balance 驗證，待有測資的代理帳號再補。
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


@pytest.fixture(scope="session")
def agent_dashboard_page(browser, site_config):
    """
    Session-scoped 已登入後台 page（**代理層級 <LU 代理帳號>，無 2FA**）。
    使用 .env 的 SITE_LU_DASHBOARD_AGENT_URL/USER/PASS（無 -admin 入口）。
    獨立 browser context；與站長 dashboard_page 不同帳號，互不互踢。
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

    # 登入前先掛上 screenshotter（同站長 fixture 理由）
    sh = ScreenshotHelper(
        page, "dashboard_agent_login", "LU 後台代理登入（無 2FA）",
        site_id=site_config.site_id, category="feature",
    )
    attach_screenshotter(page, sh)
    try:
        DashboardLoginPage = get_dashboard_login_page_class(site_config.site_id)
        login = DashboardLoginPage(page, site_config.dashboard_agent_url)
        # 代理無 2FA：totp_secret 不傳（_fill_totp 偵測不到 modal 自動跳過）
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
    """代理導航測試前回到落點頁（#/member/member-management），確保起點一致。
    代理無 `#/dashboard/index`（站長專屬）；落點即會員管理頁。
    """
    agent_dashboard_page.goto(
        f"{site_config.dashboard_agent_url}#/member/member-management",
        wait_until="domcontentloaded",
    )
    agent_dashboard_page.locator(".sidebar-nav").first.wait_for(
        state="attached", timeout=15000
    )
    return agent_dashboard_page
