"""
pytest 全域設定
- 讀取 --site 參數
- 提供 site_config / page / logged_in_page fixture
- 每個測試結束後自動登出
"""

import time
import pytest
from playwright.sync_api import Page
from config.settings import get_site_config
from pages.login_page import LoginPage
from pages.home_page import HomePage


# -----------------------------------------------
# 新增 --site 命令列參數
# -----------------------------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--site",
        action="store",
        default=None,
        help="指定測試站點，例如：--site=wlj",
    )


# -----------------------------------------------
# 每個測試結束後：嘗試登出，再等 3 秒
# -----------------------------------------------
@pytest.fixture(autouse=True)
def auto_logout_after_test(page: Page):
    yield
    try:
        home = HomePage(page)
        # 如果頭像存在代表還在登入狀態，執行登出
        if home.avatar.is_visible(timeout=2000):
            home.logout()
    except Exception:
        pass  # 未登入或已登出，略過
    time.sleep(3)


# -----------------------------------------------
# Fixtures
# -----------------------------------------------
@pytest.fixture(scope="session")
def site_config(request):
    """讀取站點設定（整個 session 共用）"""
    site_id = request.config.getoption("--site")
    return get_site_config(site_id)


@pytest.fixture(scope="function")
def login_page(page: Page, site_config):
    """提供 LoginPage 實例"""
    return LoginPage(page, site_config.url)


@pytest.fixture(scope="function")
def logged_in_page(page: Page, site_config):
    """
    已登入狀態的 fixture
    測試需要登入後才能執行的功能時使用這個
    """
    login = LoginPage(page, site_config.url)
    login.goto_and_login(site_config.username, site_config.password)

    home = HomePage(page)
    home.verify_login_success(site_config.username)
    home.dismiss_any_popups()

    return page
