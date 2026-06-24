"""
rf 站點測試專用 conftest（金爺娛樂城）
- 覆寫 site_config fixture，讓 tests/rf/ 下的測試不需加 --site=rf 即可執行
- 不覆寫 page fixture：RF 無特殊 MutationObserver 需求；
  全域 conftest.py 注入的 observer（button.toast-confirm-btn）對 RF 是 no-op（selector 不匹配）。
- 覆寫 go_home fixture：每個 functional test 前回首頁並清掉 base-modal 彈窗
"""

import pytest
from config.settings import get_site_config
from pages.factory import get_home_page_class


@pytest.fixture(scope="session")
def site_config():
    """固定使用 rf 站設定"""
    return get_site_config("rf")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """
    [RF 覆寫] 每個測試前回到首頁並清理 base-modal 彈窗。
    使用 HomePage.dismiss_any_popups() 清除 .base-modal__container 確認彈窗。
    """
    pg = class_logged_in_page
    pg.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)

    HomeCls = get_home_page_class("rf")
    home = HomeCls(pg)
    home.dismiss_any_popups()

    yield
