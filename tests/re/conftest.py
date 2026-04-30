"""
re 站點測試專用 conftest (BeWin)
- 覆寫 site_config fixture，讓 tests/re/ 下的測試不需加 --site=re 即可執行
- 不覆寫 page fixture：RE 警告彈窗用 `<button>確定</button>`（非
  toast-confirm-btn class），全域 MutationObserver 對 RE 是 no-op，可沿用。
  錯誤彈窗的處理寫在 LoginPage._handle_post_login_popup（檢測「警告」文字後跳過）。
- 覆寫 go_home fixture：每個 functional test 前回首頁並清掉伺服器錯誤 / 公告彈窗。
"""

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from config.settings import get_site_config
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present


@pytest.fixture(scope="session")
def site_config():
    """固定使用 re 站設定"""
    return get_site_config("re")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """
    [RE 覆寫] 每個測試前回到首頁並清理彈窗。
    在全域版本基礎上額外 dismiss 公告輪播彈窗（RE 與 RC 共用平台，每次進首頁都會出現）。
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
