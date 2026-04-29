"""
lt 站點測試專用 conftest
- 覆寫 site_config fixture，讓 tests/lt/ 下的測試不需加 --site=lt 即可執行
- 覆寫 page fixture：LT 已改為 WAP（mobile web）版，需以 mobile context 運行
  - 2026-04-21 audit：dev-notes/lt-wap-audit-2026-04-21.md
  - 裝置對標 iPhone 13（390×844, DPR=3, isMobile=True, hasTouch=True）— 2020-2024 最主流 iPhone
  - lt 站無伺服器錯誤彈窗，不注入 toast-confirm-btn MutationObserver
"""

import pytest
from playwright.sync_api import Playwright
from config.settings import get_site_config


@pytest.fixture(scope="session")
def site_config():
    """固定使用 lt 站設定"""
    return get_site_config("lt")


@pytest.fixture(scope="function")
def page(playwright: Playwright, browser):
    """
    lt 站 WAP 專用 page fixture：mobile emulation。
    測試後由 auto_logout_after_test 嘗試登出並關閉 context。
    """
    iphone = playwright.devices["iPhone 13"]
    context = browser.new_context(**iphone)
    try:
        page = context.new_page()
    except BaseException:
        context.close()
        raise

    try:
        yield page
    finally:
        context.close()
