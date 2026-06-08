"""
LU 首頁各區塊測試（Dlgbet）

驗證登入後首頁主要結構區塊（selector 來源：selector-explorer probe 2026-06-08）：
1. 分類快捷 tile 區（6 個分類連結各含 h3：熱門電子/真人/捕魚/體育/棋牌/任意彩票）
2. 熱門電子遊戲 section（含遊戲卡）
3. 三個排行榜（輸贏排行/提領排行/投注排行）— LU 站首頁下方
4. 輪播 banner（carousel）

與 navigation/wallet/announcement feature 區隔：只驗首頁 body 內容區塊呈現，
不點 nav、不驗餘額導航、不測公告彈窗。go_home 已 dismiss 雙層進站公告。

LU 用 AOS（Animate On Scroll）：section 初始 `.aos-init`，進 viewport 後加 `.aos-animate`，
故 selector 用 `.relative.aos-init`（非僅 `.aos-animate`）。排行榜在頁面下方需 scroll。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.home
class TestHomePageSections:
    """LU-HOME-001 ~ 004：首頁主要區塊"""

    def test_category_shortcut_tiles(self, class_logged_in_page: Page, go_home):
        """LU-HOME-001：首頁分類快捷 tile 區顯示 6 個分類連結（各含 h3）"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        section = page.locator(".grid.grid-cols-1.gap-2").first
        section.scroll_into_view_if_needed()
        if sh: sh.capture(section, "verify_分類快捷tile區")
        expect(section).to_be_visible()
        cat_links = page.locator("a[href*='/Categories/']").filter(
            has=page.locator("h3")
        )
        assert cat_links.count() == 6, f"分類連結應為 6 個，實際 {cat_links.count()}"

    def test_hot_slots_section(self, class_logged_in_page: Page, go_home):
        """LU-HOME-002：熱門電子遊戲 section 標題可見 + 首頁遊戲卡有資料

        遊戲卡為橫向清單、巢狀於 AOS 雙層 wrapper（外層 childCount=1 + 內層 childCount=2），
        scope 進 section 取卡片不穩；改驗「熱門電子」標題可見 + 首頁遊戲卡全域 count>0。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)
        heading = page.locator("h3", has_text="熱門電子").first
        heading.scroll_into_view_if_needed()
        if sh: sh.capture(heading, "verify_熱門電子標題")
        expect(heading).to_be_visible()
        cards = page.locator(".group.flex-shrink-0.cursor-pointer")
        assert cards.count() > 0, "首頁遊戲卡不應為 0"
        if sh: sh.capture(cards.first, f"verify_遊戲卡_count{cards.count()}")
        expect(cards.first).to_be_visible()

    def test_ranking_sections(self, class_logged_in_page: Page, go_home):
        """LU-HOME-003：首頁顯示 3 個排行榜（輸贏排行/提領排行/投注排行）"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        wrapper = page.locator(".grid.grid-cols-1.gap-3.pb-m-10").first
        wrapper.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        if sh: sh.full_page("verify_排行榜_全頁")
        expect(wrapper).to_be_visible()
        cards = wrapper.locator(".flex-1.rounded-\\[20px\\].bg-shade04")
        assert cards.count() == 3, f"排行榜卡應為 3 個，實際 {cards.count()}"
        for title in ("輸贏排行", "提領排行", "投注排行"):
            heading = wrapper.locator("h2").filter(has_text=title).first
            if sh: sh.capture(heading, f"verify_排行_{title}")
            expect(heading).to_be_visible()

    def test_banner_carousel_visible(self, class_logged_in_page: Page, go_home):
        """LU-HOME-004：首頁輪播 banner（carousel）可見"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        banner = page.locator(".carousel-overflow-mask").first
        banner.scroll_into_view_if_needed()
        if sh: sh.capture(banner, "verify_輪播banner")
        expect(banner).to_be_visible()
