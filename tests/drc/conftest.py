"""
drc 站點測試專用 conftest
覆寫 site_config fixture，讓 tests/drc/ 下的測試不需加 --site=drc 即可執行
"""

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from config.settings import get_site_config
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present


@pytest.fixture(scope="session")
def site_config():
    """固定使用 drc 站設定"""
    return get_site_config("drc")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """
    [DRC 覆寫] 每個測試前回到首頁並清理彈窗。
    在全域版本基礎上額外 dismiss 公告輪播彈窗（DRC 每次進首頁都會出現）。
    """
    pg = class_logged_in_page
    pg.goto(site_config.url)
    pg.wait_for_load_state("networkidle")
    try:
        pg.locator('img[alt="Loading"]').wait_for(state="hidden", timeout=5000)
    except PlaywrightTimeoutError:
        pass
    dismiss_server_error_if_present(pg)
    dismiss_announcement_popup_if_present(pg)
    yield
