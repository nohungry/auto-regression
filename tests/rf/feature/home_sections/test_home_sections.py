"""
RF 首頁各區塊測試（金爺娛樂城）
RF-HOME-001 ~ RF-HOME-006

驗證登入後首頁主要結構區塊（selector 來源：selector-explorer probe 2026-06-17）：
1. 廣告 banner（.ad-banner）
2. 遊戲展示 tabs（.gameShowcaseSection__tab，5 個）
3. 遊戲卡 grid（.gameShowcaseSection__grid 可見，.gameShowcaseSection__card 有資料）
4. 跑馬燈（.marqueeBoxs，.marqueeBoxs__items 多條）
5. 直播主列表（.live-list .live-item，有資料）
6. Footer banner（.footerBanner）

與 navigation/wallet/announcement feature 區隔：本檔只驗首頁 body 內容區塊呈現，
不點 nav、不驗餘額導航、不測公告彈窗。go_home 已 dismiss base-modal。

eachSection（6 個 .is_mobile section）雖在 DOM 中，但 class .is_mobile 暗示這些
是行動版區塊（桌面 viewport 1920x1080 下疑似 visible:false 或 display:none）；
本測試只驗明確為桌面版的核心區塊，不對 eachSection 做 visibility assert（避免假紅燈）。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.home
class TestHomePageSections:
    """RF-HOME-001 ~ 006：首頁主要區塊"""

    def test_ad_banner_visible(self, class_logged_in_page: Page, go_home):
        """RF-HOME-001：首頁廣告 banner（.ad-banner）可見"""
        page = class_logged_in_page
        sh = get_screenshotter(page)

        banner = page.locator(".ad-banner").first
        banner.scroll_into_view_if_needed()
        if sh:
            sh.capture(banner, "verify_廣告banner")
        expect(banner).to_be_visible()

    def test_game_showcase_tabs_count(self, class_logged_in_page: Page, go_home):
        """RF-HOME-002：首頁遊戲展示 tabs 顯示 5 個分類入口（金爺獨家/活動專區/熱門遊戲/最新遊戲/推薦遊戲）

        斷言策略：
        - 驗 5 個 .gameShowcaseSection__tab 存在（不綁標題文案：tab 文字可能隨產品調整）
        - 用 count() 結構斷言，穩定且 locale-agnostic
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)

        tabs_container = page.locator(".gameShowcaseSection__tabs").first
        tabs_container.scroll_into_view_if_needed()
        if sh:
            sh.capture(tabs_container, "verify_遊戲tabs容器")

        tabs = page.locator(".gameShowcaseSection__tab")
        count = tabs.count()
        if sh:
            sh.full_page(f"verify_遊戲tabs_{count}個")
        assert count == 5, f"遊戲展示 tabs 應為 5 個，實際 {count}"

    def test_game_showcase_cards_render(self, class_logged_in_page: Page, go_home):
        """RF-HOME-003：首頁遊戲卡 grid 正常渲染（.gameShowcaseSection__card 數量 > 0）

        斷言策略：只驗 count > 0（確認 grid 有資料），不寫死特定數量（隨 tab 和資料變動）。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)

        grid = page.locator(".gameShowcaseSection__grid").first
        grid.scroll_into_view_if_needed()
        if sh:
            sh.capture(grid, "verify_遊戲卡grid")
        expect(grid).to_be_visible()

        cards = page.locator(".gameShowcaseSection__card")
        count = cards.count()
        if sh:
            sh.full_page(f"verify_遊戲卡_{count}張")
        assert count > 0, f"首頁遊戲卡不應為 0，grid 疑未渲染（count={count}）"

    def test_marquee_visible(self, class_logged_in_page: Page, go_home):
        """RF-HOME-004：首頁跑馬燈（.marqueeBoxs）可見且含多條項目"""
        page = class_logged_in_page
        sh = get_screenshotter(page)

        marquee = page.locator(".marqueeBoxs").first
        marquee.scroll_into_view_if_needed()
        if sh:
            sh.capture(marquee, "verify_跑馬燈容器")
        expect(marquee).to_be_visible()

        items = page.locator(".marqueeBoxs__items")
        count = items.count()
        if sh:
            sh.full_page(f"verify_跑馬燈項目_{count}條")
        assert count > 0, f"跑馬燈項目不應為 0（count={count}）"

    def test_live_section_has_items(self, class_logged_in_page: Page, go_home):
        """RF-HOME-005：首頁直播主列表（.live-list .live-item）有資料

        斷言策略：只驗 count > 0（確認直播區有資料），不寫死特定主播數量（動態）。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)

        live_list = page.locator(".live-list.is-scrollable").first
        live_list.scroll_into_view_if_needed()
        if sh:
            sh.capture(live_list, "verify_直播主列表容器")
        expect(live_list).to_be_visible()

        live_items = page.locator(".live-item")
        count = live_items.count()
        if sh:
            sh.full_page(f"verify_直播主_{count}個")
        assert count > 0, f"直播主列表不應為 0（count={count}）"

    def test_footer_banner_visible(self, class_logged_in_page: Page, go_home):
        """RF-HOME-006：Footer banner（.footerBanner）可見"""
        page = class_logged_in_page
        sh = get_screenshotter(page)

        footer_banner = page.locator(".footerBanner").first
        footer_banner.scroll_into_view_if_needed()
        if sh:
            sh.capture(footer_banner, "verify_footer_banner")
        expect(footer_banner).to_be_visible()
