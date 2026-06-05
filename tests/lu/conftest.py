"""
lu 站點測試專用 conftest（Dlgbet）
- 覆寫 site_config fixture，讓 tests/lu/ 下的測試不需加 --site=lu 即可執行
- 覆寫 go_home fixture：每個 functional test 前回首頁並清掉進站雙層彈窗
"""

import pytest
from config.settings import get_site_config
from pages.factory import get_home_page_class


@pytest.fixture(scope="session")
def site_config():
    """固定使用 lu 站設定"""
    return get_site_config("lu")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """
    [LU 覆寫] 每個測試前回到首頁並清理進站雙層彈窗（圖片廣告 + 文字公告）。
    """
    pg = class_logged_in_page
    pg.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)

    HomeCls = get_home_page_class("lu")
    home = HomeCls(pg)
    home.dismiss_any_popups()

    yield
