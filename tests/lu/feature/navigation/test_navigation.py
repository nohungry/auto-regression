"""
LU 導覽列功能測試（Dlgbet）
LU-TC-N01 ~ LU-TC-N06

驗證 6 個遊戲分類連結點擊後 pathname 正確跳轉（probe 2026-06-06）：
- slots / casino / fishing / sport / poker / lottery

注意（與 LG 差異）：
- LU nav 為 **href-based**（`a[href='/Categories/<x>']`），無 LG 的 `ul.nav-item`。
- 體育是 `sport`（單數，與 LG 的 sports 複數不同）。
- 分類頁會附 query params（gamePlatformId 等）→ 只比 pathname。
- click_nav_item 用 dispatch_event 繞過 fresh 載入 ~10s 才出現的進站公告 mask。
"""

from urllib.parse import urlparse
import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lu")

# 遊戲分類 pathname（LU 用 href 直接導航）
NAV_PATHS = [
    "/Categories/slots",
    "/Categories/casino",
    "/Categories/fishing",
    "/Categories/sport",
    "/Categories/poker",
    "/Categories/lottery",
]


@pytest.mark.p1
@pytest.mark.lu
class TestNavigation:
    """LU 導覽列點擊跳轉驗證（class_logged_in_page + go_home）"""

    @pytest.mark.parametrize(
        "path", NAV_PATHS, ids=[p.rsplit("/", 1)[-1] for p in NAV_PATHS]
    )
    def test_nav_category_navigates(self, class_logged_in_page: Page, go_home, path):
        """LU-TC-N0x：點擊 nav 分類連結後 pathname 跳轉至對應 /Categories/<x>"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_nav_item(path)

        # 只比對 pathname（分類頁會附 query params）；wait_for_url 接受 predicate
        page.wait_for_url(lambda url: urlparse(url).path == path, timeout=8000)
        if sh: sh.full_page(f"verify_{path.rsplit('/', 1)[-1]}_分類頁載入")
