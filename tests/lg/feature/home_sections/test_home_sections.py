"""
LG 首頁各區塊測試（大撈家娛樂城）

驗證登入後首頁主要結構區塊（selector 來源：selector-explorer probe 2026-06-08）：
1. 輪播 banner（swiper-creative）
2. 熱門遊戲 section（眾多熱門遊戲 / POPULAR 標題）
3. 首頁分類 tile grid（7 個：電子遊戲/真人視訊/捕魚/棋牌/體育/彩票/鬥雞）
4. provider 遊戲卡（platform-block）有資料

與 navigation/wallet/announcement feature 區隔：本檔只驗首頁 body 內容區塊呈現，
不點 nav、不驗餘額導航、不測公告彈窗。

LG dev 環境 fade-leave-active mask 殘留（opacity:0、pointer-events:auto）：本檔只做
visibility 斷言與 scroll，不點擊，故不受殘留 mask 攔截影響。go_home 已 dismiss 公告。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.lg
@pytest.mark.home
class TestHomePageSections:
    """LG-HOME-001 ~ 004：首頁主要區塊"""

    def test_banner_carousel_visible(self, class_logged_in_page: Page, go_home):
        """LG-HOME-001：首頁輪播 banner（swiper-creative）可見"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        banner = page.locator(".mx-auto.w-full.overflow-hidden .swiper.swiper-creative").first
        banner.scroll_into_view_if_needed()
        if sh: sh.capture(banner, "verify_輪播banner")
        expect(banner).to_be_visible()

    def test_popular_section_visible(self, class_logged_in_page: Page, go_home):
        """LG-HOME-002：熱門遊戲 section（眾多熱門遊戲 / POPULAR 標題）可見"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        section = page.locator(".mx-auto.mb-5.mt-\\[60px\\].max-w-\\[1320px\\]").first
        section.scroll_into_view_if_needed()
        if sh: sh.capture(section, "verify_熱門遊戲section")
        expect(section).to_be_visible()
        expect(section.locator("p").filter(has_text="眾多熱門遊戲").first).to_be_visible()
        expect(section.locator("p").filter(has_text="POPULAR").first).to_be_visible()

    def test_category_tiles_grid(self, class_logged_in_page: Page, go_home):
        """LG-HOME-003：首頁分類 tile grid 顯示 7 個分類入口"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        grid = page.locator(".mb-\\[56px\\].grid.grid-cols-7").first
        grid.scroll_into_view_if_needed()
        if sh: sh.capture(grid, "verify_分類tile_grid")
        if sh: sh.full_page("verify_分類tile_grid_全頁")
        expect(grid).to_be_visible()
        tiles = grid.locator(".button-shadow")
        assert tiles.count() == 7, f"分類 tile 應為 7 個，實際 {tiles.count()}"

    def test_provider_game_cards(self, class_logged_in_page: Page, go_home):
        """LG-HOME-004：首頁 provider 遊戲卡（platform-block）有資料"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        cards = page.locator(".platform-block")
        count = cards.count()
        assert count > 0, "首頁 provider 遊戲卡不應為 0"
        cards.first.scroll_into_view_if_needed()
        if sh: sh.capture(cards.first, f"verify_provider遊戲卡_count{count}")
        expect(cards.first).to_be_visible()
