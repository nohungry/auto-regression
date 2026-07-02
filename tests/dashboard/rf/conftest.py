"""
RF 後台測試專用 conftest（金爺娛樂城，信用版）— 站長與代理皆無 2FA（2026-06-17 probe）。

session-scoped（read-only smoke）：
- dashboard_page（站長 SITE_RF_DASHBOARD_URL/USER/PASS，含 -admin）
- agent_dashboard_page（代理 SITE_RF_DASHBOARD_AGENT_URL/USER/PASS，無 -admin）
function-scoped（state-mutating 充提用，避免被 logout smoke 污染）：
- fresh_dashboard_page（站長，每測試獨立 context）

兩帳號不同（不互踢）。login fixture 共用邏輯見 utils/dashboard_helpers.py
（fixture 保持 per-site 避免 session 快取跨站污染）。
"""

import pytest
from config.settings import get_site_config
from utils.dashboard_helpers import dashboard_login_session


@pytest.fixture(scope="session")
def site_config():
    """固定使用 rf 站設定"""
    return get_site_config("rf")


@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    """站長已登入後台 page（session 共用）。RF 站長無 2FA，login 不吃 totp。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_url,
        site_config.dashboard_user, site_config.dashboard_pass,
        screenshot=("dashboard_login", "RF 後台站長登入（無 2FA）"),
    )


@pytest.fixture
def go_dashboard(dashboard_page, site_config):
    """導航測試前回站長落點頁（#/management/all-management）。非 autouse：logout 測試不需要。"""
    dashboard_page.goto(
        f"{site_config.dashboard_url}#/management/all-management",
        wait_until="domcontentloaded",
    )
    dashboard_page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=15000)
    return dashboard_page


@pytest.fixture(scope="session")
def agent_dashboard_page(browser, site_config):
    """代理已登入後台 page（session 共用；與站長不同帳號，互不互踢）。RF 代理無 2FA。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_agent_url,
        site_config.dashboard_agent_user, site_config.dashboard_agent_pass,
        screenshot=("dashboard_agent_login", "RF 後台代理登入（無 2FA）"),
    )


@pytest.fixture
def go_agent_dashboard(agent_dashboard_page, site_config):
    """代理導航測試前回落點頁（#/management/all-management，與站長相同）。"""
    agent_dashboard_page.goto(
        f"{site_config.dashboard_agent_url}#/management/all-management",
        wait_until="domcontentloaded",
    )
    agent_dashboard_page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=15000)
    return agent_dashboard_page


@pytest.fixture
def fresh_dashboard_page(browser, site_config):
    """站長已登入後台 page（function scope，充提測試用；每測試獨立 context 避免互踢/污染）。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_url,
        site_config.dashboard_user, site_config.dashboard_pass,
        screenshot=("topup_login", "RF 後台站長登入（充提測試用）"),
    )
