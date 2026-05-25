"""
qw 站點測試專用 conftest（LM來財娛樂城）
- 覆寫 site_config fixture，讓 tests/qw/ 下的測試不需加 --site=qw 即可執行
- 不覆寫 page fixture：QW 無 toast-confirm-btn MutationObserver 需求；
  但全域 conftest.py 注入的 observer 對 QW 是 no-op（selector 不匹配），可沿用。
- 覆寫 go_home fixture：每個 functional test 前回首頁並清掉彈窗
"""

import pytest
from config.settings import get_site_config
from pages.factory import get_home_page_class


@pytest.fixture(scope="session")
def site_config():
    """固定使用 qw 站設定"""
    return get_site_config("qw")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """
    [QW 覆寫] 每個測試前回到首頁並清理彈窗。
    使用 HomePage.dismiss_any_popups() 清除公告彈窗與 TOTP 提示。
    """
    pg = class_logged_in_page
    pg.goto(site_config.url, wait_until="networkidle")

    HomeCls = get_home_page_class("qw")
    home = HomeCls(pg)
    home.dismiss_any_popups()

    yield
