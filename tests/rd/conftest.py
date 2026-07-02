"""
rd 站點測試專用 conftest（狗狗娛樂城）
- 覆寫 site_config：tests/rd/ 下不需加 --site=rd。
- 不覆寫 page fixture：RD 警告彈窗非 toast-confirm-btn class，全域 observer 為 no-op。
- 覆寫 go_home：回首頁 + 清 server error / 公告，另清 RD 專屬蓋板 dialog-mask。
"""

import pytest
from config.settings import get_site_config
from utils.home_reset import reset_home_with_dismissers


@pytest.fixture(scope="session")
def site_config():
    return get_site_config("rd")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """[RD 覆寫] 回首頁 + 清彈窗；dismiss_mask=True 另清會攔截 navbar 的蓋板廣告。"""
    reset_home_with_dismissers(class_logged_in_page, site_config.url, dismiss_mask=True)
    yield
