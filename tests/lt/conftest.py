"""
lt 站點測試專用 conftest（LM來財信用網）

- 覆寫 site_config：tests/lt/ 下不需加 --site=lt 即可執行。
- **不再覆寫 page fixture**（2026-09-13）：dev-lt 換版後前台與 RC 同模板，
  伺服器錯誤彈窗也走 `button.toast-confirm-btn`，全域 MutationObserver 對 LT 有用；
  需斷言錯誤彈窗可見的負向登入測試改掛 `@pytest.mark.no_toast_observer`（與 RC 一致），
  由根 conftest 的 page fixture 對該 test 單獨停用 observer。
- 覆寫 go_home：新版首頁有 RC 型進站公告 `.popup-announcement-mask`，
  不清會全屏攔截點擊（共用 utils/home_reset）。
"""

import pytest
from config.settings import get_site_config
from utils.home_reset import reset_home_with_dismissers


@pytest.fixture(scope="session")
def site_config():
    """固定使用 lt 站設定"""
    return get_site_config("lt")


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """[LT 覆寫] 每個測試前回首頁並清 server error / 進站公告彈窗。"""
    reset_home_with_dismissers(class_logged_in_page, site_config.url)
    yield
