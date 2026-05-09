"""
rd 站點測試專用 conftest (狗狗娛樂城)
- 覆寫 site_config fixture，讓 tests/rd/ 下的測試不需加 --site=rd 即可執行
- 不覆寫 page fixture：RD 警告彈窗用 `<button>確定</button>`（非 toast-confirm-btn class），
  全域 MutationObserver 對 RD 是 no-op，可沿用。
- 覆寫 go_home fixture：每個 functional test 前回首頁並清掉伺服器錯誤 / 公告彈窗。
"""

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from config.settings import get_site_config
from utils.dialog_helper import (
    dismiss_server_error_if_present,
    dismiss_announcement_popup_if_present,
    dismiss_dialog_mask_if_present,
)


@pytest.fixture(scope="session")
def site_config():
    """固定使用 rd 站設定"""
    return get_site_config("rd")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """
    [RD 覆寫] 每個測試前回到首頁並清理彈窗。
    沿用 rc/re pattern。
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
    # RD 站專屬蓋板廣告（.dialog-mask + .dialog-container），會攔截 navbar 點擊
    dismiss_dialog_mask_if_present(pg)
    yield
