"""
ks 站點測試專用 conftest（Super9娛樂城）
- 覆寫 site_config fixture，讓 tests/ks/ 下的測試不需加 --site=ks 即可執行
- 覆寫 go_home fixture：每個 functional test 前回首頁並清掉進站公告彈窗
"""

import pytest
from config.settings import get_site_config
from pages.factory import get_home_page_class


@pytest.fixture(scope="session")
def site_config():
    """固定使用 ks 站設定"""
    return get_site_config("ks")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """
    [KS 覆寫] 每個測試前回到首頁並清理進站公告彈窗。
    """
    pg = class_logged_in_page
    pg.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)

    HomeCls = get_home_page_class("ks")
    home = HomeCls(pg)
    home.dismiss_any_popups()

    yield
