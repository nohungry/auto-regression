"""
lt 站點測試專用 conftest
- 覆寫 site_config fixture，讓 tests/lt/ 下的測試不需加 --site=lt 即可執行
- 覆寫 page fixture：LT 2026-05-18 換版改回 desktop responsive，沿用 RC/RE/RD 的
  CDP maximize 模式（不再用 iPhone 13 mobile emulation）；但**不注入** 全域的
  toast-confirm-btn MutationObserver，因為 LT 的錯誤 dialog（密碼錯/帳號錯）
  確定按鈕也叫 button.toast-confirm-btn，被 observer 秒關會讓 wrong_password /
  wrong_username 測試 assert 不到 dialog。
"""

import pytest
from playwright.sync_api import Playwright
from config.settings import get_site_config


@pytest.fixture(scope="session")
def site_config():
    """固定使用 lt 站設定"""
    return get_site_config("lt")


@pytest.fixture(scope="function")
def page(browser):
    """
    lt 站 desktop responsive page fixture：CDP maximize + 不注入 observer。

    與全域 _new_configured_page 邏輯相同，但拿掉 toast-confirm-btn observer
    （LT 錯誤 dialog 用同一個 selector，注入會破壞錯誤路徑測試）。
    """
    context = browser.new_context(no_viewport=True)
    try:
        pg = context.new_page()

        cdp = context.new_cdp_session(pg)
        window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
        cdp.send("Browser.setWindowBounds", {
            "windowId": window_id,
            "bounds": {"windowState": "maximized"},
        })
        cdp.detach()
    except BaseException:
        context.close()
        raise

    try:
        yield pg
    finally:
        context.close()
