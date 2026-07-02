"""
qw 站點測試專用 conftest（LM來財娛樂城）
- 覆寫 site_config：tests/qw/ 下不需加 --site=qw。
- 覆寫 go_home：回首頁（networkidle）+ HomePage.dismiss_any_popups() 清公告/TOTP 提示。
"""

import pytest
from config.settings import get_site_config
from utils.home_reset import reset_home_with_home_popups


@pytest.fixture(scope="session")
def site_config():
    return get_site_config("qw")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """[QW 覆寫] 回首頁並清彈窗；QW 用 networkidle（timeout 30s 保持原行為）。"""
    reset_home_with_home_popups(
        class_logged_in_page, site_config.url, "qw",
        wait_until="networkidle", timeout=30000,
    )
    yield
