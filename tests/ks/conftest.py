"""
ks 站點測試專用 conftest（Super9娛樂城／進站公告）
- 覆寫 site_config：tests/ks/ 下不需加 --site=ks。
- 覆寫 go_home：回首頁 + 委由該站 HomePage.dismiss_any_popups() 清彈窗（共用 utils/home_reset）。
"""

import pytest
from config.settings import get_site_config
from utils.home_reset import reset_home_with_home_popups


@pytest.fixture(scope="session")
def site_config():
    return get_site_config("ks")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """[KS 覆寫] 每個測試前回首頁並清進站彈窗。"""
    reset_home_with_home_popups(class_logged_in_page, site_config.url, "ks")
    yield
