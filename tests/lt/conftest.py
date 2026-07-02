"""
lt 站點測試專用 conftest
- 覆寫 site_config fixture，讓 tests/lt/ 下的測試不需加 --site=lt 即可執行
- 覆寫 page fixture：沿用全域 _new_configured_page 的 CDP maximize，但**不注入**
  toast-confirm-btn MutationObserver — LT 的錯誤 dialog（密碼錯/帳號錯）確定按鈕
  也叫 button.toast-confirm-btn，被 observer 秒關會讓 wrong_password / wrong_username
  測試 assert 不到 dialog。故傳 install_toast_observer=False。
- 不覆寫 go_home：沿用全域版（root conftest.py）。
"""

import pytest
from config.settings import get_site_config
from conftest import _new_configured_page


@pytest.fixture(scope="session")
def site_config():
    """固定使用 lt 站設定"""
    return get_site_config("lt")


@pytest.fixture(scope="function")
def page(browser):
    """lt page fixture：與全域相同（CI viewport / 本機 CDP maximize），但不注入
    toast-confirm-btn observer（LT 錯誤 dialog 用同一 selector，注入會破壞錯誤路徑測試）。
    """
    context, pg = _new_configured_page(browser, install_toast_observer=False)
    try:
        yield pg
    finally:
        context.close()
