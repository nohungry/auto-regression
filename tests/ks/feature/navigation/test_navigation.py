"""
KS 導覽列功能測試（Super9娛樂城）
KS-TC-N01 ~ KS-TC-N06

驗證 6 個遊戲分類點擊後 pathname 正確跳轉（probe 2026-06-06）：
- slots / casino / sports / fishing / mini-game / lottery

注意：
- KS nav 為 `ul.nav-item li` 內含 `<a href>`（簡體中文：电子/真人/体育/捕鱼/小游戏/彩票）。
- 体育是 `sports`（複數）；小游戏是 `mini-game`（連字號）。
- 「优惠活动」→ /promotions（非遊戲分類，本檔不涵蓋）。
- 分類頁附 query params → 只比 pathname；click_nav_item dispatch 繞過晚出現公告 mask。
"""

from urllib.parse import urlparse
import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("ks")

NAV_PATHS = [
    "/Categories/slots",
    "/Categories/casino",
    "/Categories/sports",
    "/Categories/fishing",
    "/Categories/mini-game",
    "/Categories/lottery",
]


@pytest.mark.p1
@pytest.mark.ks
class TestNavigation:
    """KS 導覽列點擊跳轉驗證（class_logged_in_page + go_home）"""

    @pytest.mark.parametrize(
        "path", NAV_PATHS, ids=[p.rsplit("/", 1)[-1] for p in NAV_PATHS]
    )
    def test_nav_category_navigates(self, class_logged_in_page: Page, go_home, path):
        """KS-TC-N0x：點擊 nav 分類後 pathname 跳轉至對應 /Categories/<x>"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_nav_item(path)

        page.wait_for_url(lambda url: urlparse(url).path == path, timeout=8000)
        if sh: sh.full_page(f"verify_{path.rsplit('/', 1)[-1]}_分類頁載入")
