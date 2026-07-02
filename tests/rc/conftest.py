"""
rc 站點測試專用 conftest（王老吉娛樂城）
- 覆寫 site_config：tests/rc/ 下不需加 --site=rc。
- 不覆寫 page fixture：rc 警告彈窗非 toast-confirm-btn class，全域 observer 為 no-op。
- 覆寫 go_home：回首頁 + 清 server error / 公告彈窗（共用 utils/home_reset）。
"""

import pytest
from config.settings import get_site_config
from utils.home_reset import reset_home_with_dismissers


@pytest.fixture(scope="session")
def site_config():
    return get_site_config("rc")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """[RC 覆寫] 每個測試前回首頁並清 server error / 公告輪播彈窗。"""
    reset_home_with_dismissers(class_logged_in_page, site_config.url)
    yield
