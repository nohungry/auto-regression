"""
lg 站點測試專用 conftest（大撈家娛樂城）
- 覆寫 site_config fixture，讓 tests/lg/ 下的測試不需加 --site=lg 即可執行
- 不覆寫 page fixture：LG 無特殊 MutationObserver 需求；
  全域 conftest.py 注入的 observer 對 LG 是 no-op（selector 不匹配），可沿用。
- 覆寫 go_home fixture：每個 functional test 前回首頁並清掉進站公告彈窗
"""

import pytest
from config.settings import get_site_config
from pages.factory import get_home_page_class


@pytest.fixture(scope="session")
def site_config():
    """固定使用 lg 站設定"""
    return get_site_config("lg")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """
    [LG 覆寫] 每個測試前回到首頁並清理進站公告彈窗。
    使用 HomePage.dismiss_any_popups() 清除 .dialog-container.w-full 公告。
    """
    pg = class_logged_in_page
    pg.goto(site_config.url, wait_until="domcontentloaded")

    HomeCls = get_home_page_class("lg")
    home = HomeCls(pg)
    home.dismiss_any_popups()

    yield
