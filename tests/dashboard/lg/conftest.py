"""
LG 後台測試專用 conftest（大撈家娛樂城，Vue admin）

- agent_dashboard_page（代理 SITE_LG_DASHBOARD_AGENT_USER/PASS，無 -admin，無 2FA）+ go_agent_dashboard；
  LG 代理為空帳號 → 只 read-only smoke。
- dashboard_page（站長 SITE_LG_DASHBOARD_USER/PASS + TOTP，-admin 入口；供主錢包 top_up）。

兩帳號不同（不互踢）。login fixture 共用邏輯見 utils/dashboard_helpers.py
（fixture 保持 per-site 避免 session 快取跨站污染）。
"""

import pytest
from config.settings import get_site_config
from utils.dashboard_helpers import dashboard_login_session


@pytest.fixture(scope="session")
def site_config():
    """固定使用 lg 站設定"""
    return get_site_config("lg")


@pytest.fixture(scope="session")
def agent_dashboard_page(browser, site_config):
    """代理已登入後台 page（無 2FA，agent_totp 條件式自動跳過；session 共用）。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_agent_url,
        site_config.dashboard_agent_user, site_config.dashboard_agent_pass,
        totp=site_config.dashboard_agent_totp,
        screenshot=("dashboard_agent_login", "LG 後台代理登入（無 2FA）"),
    )


@pytest.fixture
def go_agent_dashboard(agent_dashboard_page, site_config):
    """代理導航測試前回落點頁（#/member/member-management）。"""
    agent_dashboard_page.goto(
        f"{site_config.dashboard_agent_url}#/member/member-management",
        wait_until="domcontentloaded",
    )
    agent_dashboard_page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=15000)
    return agent_dashboard_page


@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    """站長已登入後台 page（含 TOTP 2FA，-admin 入口；與代理不同帳號，互不互踢）。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_url,
        site_config.dashboard_user, site_config.dashboard_pass,
        totp=site_config.dashboard_totp,
        screenshot=("dashboard_login_2fa", "LG 後台站長登入（含 TOTP 2FA）"),
    )
