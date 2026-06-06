"""
LG 導覽列功能測試（大撈家娛樂城）
LG-TC-N01 ~ LG-TC-N07

驗證 7 個遊戲主分類點擊後 pathname 正確跳轉（probe 2026-06-06）：
- 電子 → /Categories/slots
- 真人 → /Categories/casino
- 捕魚 → /Categories/fishing
- 棋牌 → /Categories/poker
- 體育 → /Categories/sports        （複數，與 RD 的單數 sport 不同）
- 彩票 → /Categories/lottery
- 鬥雞 → /Categories/cock-fighting  （連字號，與 RD 的 cockfighting 不同）

注意：
- 分類頁會附 query params（gamePlatformId/multiples），故只比對 pathname，不比完整 URL。
- 「熱門/優惠/公告」非遊戲分類（hot/promotions/announcement），本檔不涵蓋。
- nav 在 `ul.nav-item li`，每分類文字唯一（無 RC 的 hidden 重複節點問題）。
"""

from urllib.parse import urlparse
import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lg")

# (分類中文名, 預期 pathname)
NAV_CASES = [
    ("電子", "/Categories/slots"),
    ("真人", "/Categories/casino"),
    ("捕魚", "/Categories/fishing"),
    ("棋牌", "/Categories/poker"),
    ("體育", "/Categories/sports"),
    ("彩票", "/Categories/lottery"),
    ("鬥雞", "/Categories/cock-fighting"),
]


@pytest.mark.p1
@pytest.mark.lg
class TestNavigation:
    """LG 導覽列點擊跳轉驗證

    使用 class_logged_in_page + go_home：每個 test 前回首頁並關掉進站公告蓋板
    （go_home 的 dismiss_any_popups 已等 mask pointer-events 清除，避免擋點擊）。
    """

    @pytest.mark.parametrize(
        "category, expected_path",
        NAV_CASES,
        ids=[c[1].rsplit("/", 1)[-1] for c in NAV_CASES],
    )
    def test_nav_category_navigates(
        self, class_logged_in_page: Page, go_home, category, expected_path
    ):
        """LG-TC-N0x：點擊 nav 分類後 pathname 跳轉至對應 /Categories/<x>"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_nav_item(category)

        # 只比對 pathname（分類頁會附 gamePlatformId 等 query params，比完整 URL 會 flaky）。
        # 用 wait_for_url（接受 predicate）；to_have_url 只收 string/regex 不可傳 lambda。
        page.wait_for_url(
            lambda url: urlparse(url).path == expected_path, timeout=8000
        )
        if sh: sh.full_page(f"verify_{category}_分類頁載入")
