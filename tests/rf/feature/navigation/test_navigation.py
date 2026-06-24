"""
RF 導覽列功能測試（金爺娛樂城）
RF-TC-N01 ~ RF-TC-N04

probe 結果（dev-rf，2026-06-17）：
- nav.menu_nav 內只有 3 個 button（真人/電子/捕魚）+ 1 個 a（首頁）
  沒有體育/彩票/棋牌，故不涵蓋這些分類
- URL pattern：
    真人  → /Categories/casino
    電子  → /Categories/slots
    捕魚  → /Categories/fishing
  URL 後附 #gameShowcaseSection__header fragment（pathname 比對即可）
- 廳館卡片 selector：span.gameShowcaseSection__name（精確 class，含廳館名稱文字）
  實機確認有 4 個：T9真人 / DG真人 / MT真人 / 歐博
  span.gameShowcaseSection__card 也包含廳館名，但 .gameShowcaseSection__name 更精確
- LI.custom-select__list 下也有廳館文字，但 visible=False（下拉選單隱藏），不可用
"""

from urllib.parse import urlparse
import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("rf")

# (分類中文名, 預期 pathname)
NAV_CASES = [
    ("真人", "/Categories/casino"),
    ("電子", "/Categories/slots"),
    ("捕魚", "/Categories/fishing"),
]

# 真人廳館卡片（probe 2026-06-17 實機確認）
CASINO_HALLS = ["T9真人", "DG真人", "MT真人", "歐博"]


@pytest.mark.p1
@pytest.mark.rf
class TestNavigation:
    """RF 導覽列點擊跳轉驗證

    使用 class_logged_in_page + go_home：每個 test 前回首頁並清掉 base-modal 彈窗
    （go_home 的 dismiss_any_popups 已處理 base-modal 確認鍵）。
    """

    @pytest.mark.parametrize(
        "category, expected_path",
        NAV_CASES,
        ids=[c[1].rsplit("/", 1)[-1] for c in NAV_CASES],
    )
    def test_nav_category_navigates(
        self, class_logged_in_page: Page, go_home, category, expected_path
    ):
        """RF-TC-N0x：點擊 nav 分類後 pathname 跳轉至對應 /Categories/<x>

        斷言策略：
        - 只比對 pathname（URL 後附 #gameShowcaseSection__header fragment，比完整 URL 會 flaky）
        - 用 wait_for_url predicate 等待 URL 跳轉
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_nav_item(category)

        # 只比對 pathname（URL 後附 fragment，比完整 URL 會 flaky）
        page.wait_for_url(
            lambda url: urlparse(url).path == expected_path, timeout=8000
        )
        if sh:
            sh.full_page(f"verify_{category}_分類頁載入")

    def test_casino_halls_visible(self, class_logged_in_page: Page, go_home):
        """RF-TC-N04：真人分類頁顯示所有廳館（T9真人、DG真人、MT真人、歐博）

        斷言策略：
        - 點 nav 真人後等 pathname = /Categories/casino
        - 每個廳館名稱的 span.gameShowcaseSection__name 可見
        - .gameShowcaseSection__name 為廳館卡片的精確 class（probe 確認 visible=True）
          有別於 LI.custom-select__list 下同名 LI（visible=False，不可用）
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_nav_item("真人")
        page.wait_for_url(
            lambda url: urlparse(url).path == "/Categories/casino", timeout=8000
        )

        if sh:
            sh.full_page("verify_真人分類頁載入")

        for hall in CASINO_HALLS:
            # span.gameShowcaseSection__name 為廳館卡片精確 class，每廳一個
            el = page.locator("span.gameShowcaseSection__name", has_text=hall).first
            el.scroll_into_view_if_needed()
            if sh:
                sh.capture(el, f"verify_廳館_{hall}")
            from playwright.sync_api import expect
            expect(el).to_be_visible(timeout=8000)
