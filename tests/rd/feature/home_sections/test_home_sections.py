"""
RD 首頁各區塊測試 (狗狗娛樂城)

驗證登入後首頁的主要結構區塊：
1. 6 個分類 tile（電子/真人/捕魚/體育/彩票/鬥雞）— 上方主導覽
2. 3 個遊戲清單 section（電子/真人/體育）— 中段含「View all」連結
3. 2 個排行 H2 section（輸贏排行/投注排行）— RD 站獨有

與 RC 差異：
- RD 沒有跑馬燈公告（announcement marquee 不存在）
- RD navbar 不顯示餘額（藏在「個人資訊」面板內），餘額測試另行 `wallet/` feature 處理
- RD 多出「輸贏排行/投注排行」H2 sections
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.home
class TestHomePageSections:
    """RD 首頁主要區塊驗證"""

    def test_category_tiles_visible(self, class_logged_in_page: Page, go_home):
        """RD-TC-H01：首頁顯示 6 個分類 tile（電子/真人/捕魚/體育/彩票/鬥雞）"""
        page = class_logged_in_page
        sh = get_screenshotter(page)

        # 6 個 tile 對應 6 個 H3，搭配父層 class 鎖定（避免命中中段 game-list section H3）
        # 父 class 為 `mb-4 flex items-center gap-...`，與中段 `flex items-center gap-3`（無 mb-4）區分
        categories = ["電子", "真人", "捕魚", "體育", "彩票", "鬥雞"]
        if sh: sh.full_page("verify_首頁分類tile_全貌")

        for cat in categories:
            tile = page.locator("div.mb-4 h3", has_text=cat).first
            tile.scroll_into_view_if_needed()
            if sh: sh.capture(tile, f"verify_分類tile_{cat}")
            expect(tile).to_be_visible()

    def test_game_list_sections_visible(self, class_logged_in_page: Page, go_home):
        """RD-TC-H02：首頁中段 3 個遊戲清單 section（電子/真人/體育）含「View all」連結

        Section header 容器為 `div.mb-4.flex.items-center.justify-between`，
        包含 H3 標題與 "View all" 連結；用 `justify-between` 與上方 tile 區分。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)

        sections = ["電子", "真人", "體育"]
        if sh: sh.full_page("verify_遊戲清單section_全貌")

        for sec in sections:
            section_header = page.locator(
                "div.mb-4.flex.items-center.justify-between", has_text=sec
            ).first
            section_header.scroll_into_view_if_needed()
            if sh: sh.capture(section_header, f"verify_遊戲清單_{sec}_含ViewAll")
            expect(section_header).to_be_visible()
            # 確認 View all 按鈕存在於該 section 內
            view_all = section_header.locator("a", has_text="View all").first
            expect(view_all).to_be_visible()

    def test_ranking_sections_visible(self, class_logged_in_page: Page, go_home):
        """RD-TC-H03：首頁顯示 2 個排行 H2 section（輸贏排行/投注排行）— RD 站獨有"""
        page = class_logged_in_page
        sh = get_screenshotter(page)

        rankings = ["輸贏排行", "投注排行"]
        # 排行 section 在頁面下方，先 scroll
        page.evaluate("window.scrollBy(0, 800)")
        page.wait_for_timeout(500)
        if sh: sh.full_page("verify_排行section_全貌")

        for rank in rankings:
            heading = page.locator("h2", has_text=rank).first
            heading.scroll_into_view_if_needed()
            if sh: sh.capture(heading, f"verify_排行section_{rank}")
            expect(heading).to_be_visible()
