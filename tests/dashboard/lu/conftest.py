"""
LU 後台測試專用 conftest（Dlgbet，現金版 Vue admin）

- dashboard_page（站長 SITE_LU_DASHBOARD_USER/PASS + TOTP 2FA，-admin 入口）；落點 #/dashboard/index。
- agent_dashboard_page（代理 SITE_LU_DASHBOARD_AGENT_USER/PASS + AGENT_TOTP，**2026-06-25 起代理也強制 2FA**）；
  落點 #/member/member-management。

兩帳號不同（不互踢）；代理為空帳號故只 read-only smoke。login fixture 共用邏輯見
utils/dashboard_helpers.py（fixture 保持 per-site 避免 session 快取跨站污染）。
"""

import pytest
from config.settings import get_site_config
from utils.dashboard_helpers import dashboard_login_session


@pytest.fixture(scope="session")
def site_config():
    """固定使用 lu 站設定"""
    return get_site_config("lu")


@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    """站長已登入後台 page（含 TOTP 2FA；session 共用，避免頻繁登入觸發 rate-limit）。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_url,
        site_config.dashboard_user, site_config.dashboard_pass,
        totp=site_config.dashboard_totp,
        screenshot=("dashboard_login_2fa", "LU 後台登入（含 TOTP 2FA）"),
    )


@pytest.fixture
def go_dashboard(dashboard_page, site_config):
    """導航測試前回站長儀表板首頁（#/dashboard/index）。非 autouse：logout 測試不需要。"""
    dashboard_page.goto(
        f"{site_config.dashboard_url}#/dashboard/index",
        wait_until="domcontentloaded",
    )
    dashboard_page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=15000)
    return dashboard_page


@pytest.fixture(scope="session")
def agent_dashboard_page(browser, site_config):
    """代理已登入後台 page（2026-06-25 起強制 2FA，帶 agent_totp；與站長不同帳號，互不互踢）。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_agent_url,
        site_config.dashboard_agent_user, site_config.dashboard_agent_pass,
        totp=site_config.dashboard_agent_totp,  # 條件式：站點若再撤 2FA 也不會壞
        screenshot=("dashboard_agent_login", "LU 後台代理登入（含 2FA）"),
    )


@pytest.fixture
def go_agent_dashboard(agent_dashboard_page, site_config):
    """代理導航測試前回落點頁（#/member/member-management；代理無站長專屬 dashboard/index）。"""
    agent_dashboard_page.goto(
        f"{site_config.dashboard_agent_url}#/member/member-management",
        wait_until="domcontentloaded",
    )
    agent_dashboard_page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=15000)
    return agent_dashboard_page
