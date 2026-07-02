"""
lg 站點測試專用 conftest（大撈家娛樂城／進站公告 .dialog-container.w-full）
- 覆寫 site_config：tests/lg/ 下不需加 --site=lg。
- 覆寫 go_home：回首頁 + 委由該站 HomePage.dismiss_any_popups() 清彈窗（共用 utils/home_reset）。
"""

import pytest
from config.settings import get_site_config
from utils.home_reset import reset_home_with_home_popups


@pytest.fixture(scope="session")
def site_config():
    return get_site_config("lg")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """[LG 覆寫] 每個測試前回首頁並清進站彈窗。"""
    reset_home_with_home_popups(class_logged_in_page, site_config.url, "lg")
    yield
