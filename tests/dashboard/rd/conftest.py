"""
RD 後台測試專用 conftest（狗狗娛樂城，信用版 /management 後台）
- dashboard_page：代理 SITE_RD_DASHBOARD_AGENT_USER/PASS（走無 -admin 代理入口 agent_url，無 2FA）
- master_dashboard_page：總代/站長 SITE_RD_DASHBOARD_USER/PASS（供總代→代理派點，無 2FA）
- go_management（autouse）：每個 test 前回管理頁
- RD dialog 有操作者密碼欄（測試檔傳 operator_password，非此 conftest 處理）

login fixture 共用邏輯見 utils/dashboard_helpers.py（fixture 保持 per-site 避免
session 快取跨站污染）。
"""

import pytest
from config.settings import get_site_config
from utils.dashboard_helpers import dashboard_login_session


@pytest.fixture(scope="session")
def site_config():
    """固定使用 rd 站設定"""
    return get_site_config("rd")


@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    """代理帳號已登入後台 page（走代理入口 agent_url；session 共用，獨立 context）。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_agent_url,
        site_config.dashboard_agent_user, site_config.dashboard_agent_pass,
        totp=site_config.dashboard_agent_totp,  # 代理 2FA（RD 目前無，條件式跳過）
    )


@pytest.fixture(scope="session")
def master_dashboard_page(browser, site_config):
    """總代/站長帳號已登入後台 page（供總代→代理派點；與代理不同帳號，互不互踢）。"""
    yield from dashboard_login_session(
        browser, site_config, site_config.dashboard_url,
        site_config.dashboard_user, site_config.dashboard_pass,
        totp=site_config.dashboard_totp,
    )


@pytest.fixture(autouse=True)
def go_management(dashboard_page, site_config):
    """每個 test 前回管理頁。Vue SPA 有 websocket 長連線，用 domcontentloaded + 等 tab 出現。"""
    dashboard_page.goto(
        f"{site_config.dashboard_agent_url}#/management/all-management",
        wait_until="domcontentloaded",
    )
    dashboard_page.locator('button.tab-btn').first.wait_for(state="attached", timeout=15000)
