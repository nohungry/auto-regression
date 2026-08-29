"""
QW 後台測試專用 conftest（LM來財娛樂城，Vue admin）

- agent_dashboard_page（代理 SITE_QW_DASHBOARD_AGENT_USER/PASS + AGENT_TOTP，無 -admin）+ go_agent_dashboard；
  ⚠️ QW 代理**需 2FA**（與 LU/LG/KS 代理不同）；QW 代理為空帳號 → 只 read-only smoke。
- dashboard_page（站長 SITE_QW_DASHBOARD_USER/PASS + TOTP，-admin 入口；供主錢包 top_up）。

兩帳號不同（不互踢）；2FA 帳號整 session 只登入一次避免 rate-limit。login fixture
共用邏輯見 utils/dashboard_helpers.py（fixture 保持 per-site 避免 session 快取跨站污染）。
"""

import pytest
from config.settings import get_site_config
from utils.dashboard_helpers import dashboard_login_session


@pytest.fixture(scope="session")
def site_config():
    """固定使用 qw 站設定"""
    return get_site_config("qw")


@pytest.fixture(scope="session")
def agent_dashboard_page(browser, site_config):
    """代理已登入後台 page（QW 代理含 2FA，帶 agent_totp；session 共用避免 rate-limit）。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_agent_url,
        site_config.dashboard_agent_user, site_config.dashboard_agent_pass,
        totp=site_config.dashboard_agent_totp,
        screenshot=("dashboard_agent_login", "QW 後台代理登入（含 2FA）"),
    )


@pytest.fixture
def go_agent_dashboard(agent_dashboard_page, site_config):
    """代理導航測試前回落點頁（#/member/member-management）。"""
    agent_dashboard_page.goto(
        f"{site_config.dashboard_agent_url}#/member/member-management",
        wait_until="domcontentloaded",
    )
    agent_dashboard_page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=30000)
    return agent_dashboard_page


@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    """站長已登入後台 page（含 TOTP 2FA，-admin 入口；與代理不同帳號，互不互踢；session 只登入一次）。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_url,
        site_config.dashboard_user, site_config.dashboard_pass,
        totp=site_config.dashboard_totp,
        screenshot=("dashboard_login_2fa", "QW 後台站長登入（含 TOTP 2FA）"),
    )
