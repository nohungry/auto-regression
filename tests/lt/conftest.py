"""
lt 站點測試專用 conftest
- 覆寫 site_config fixture，讓 tests/lt/ 下的測試不需加 --site=lt 即可執行
- 覆寫 page fixture：lt 站無伺服器錯誤彈窗，不注入 toast-confirm-btn MutationObserver
"""

import pytest
from playwright.sync_api import Page
from config.settings import get_site_config


@pytest.fixture(scope="session")
def site_config():
    """固定使用 lt 站設定"""
    return get_site_config("lt")


@pytest.fixture(scope="function")
def page(browser):
    """
    lt 站點專用 page fixture：不注入 toast-confirm-btn MutationObserver
    （lt 站無伺服器錯誤彈窗，注入後反而干擾 SPA 登入後的頁面跳轉）
    測試後由 auto_logout_after_test 自動登出並關閉 context。
    """
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    cdp = context.new_cdp_session(page)
    window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
    cdp.send("Browser.setWindowBounds", {
        "windowId": window_id,
        "bounds": {"windowState": "maximized"},
    })
    cdp.detach()

    yield page
    context.close()
