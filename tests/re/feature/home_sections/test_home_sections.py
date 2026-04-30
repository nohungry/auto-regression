"""
RE 首頁各區塊測試 (BeWin)
熱門遊戲、最新遊戲、公告跑馬燈、餘額顯示
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.re
@pytest.mark.home
class TestHomePageSections:
    """RE-TC-016 ~ RE-TC-019：首頁各區塊"""

    def test_hot_games_section(self, class_logged_in_page: Page, go_home):
        """RE-TC-016：首頁顯示「熱門遊戲」區塊且有遊戲卡片"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        title = page.locator("text=熱門遊戲").first
        if sh: sh.capture(title, "verify_熱門遊戲標題")
        expect(title).to_be_visible()
        grid = page.locator(".mt-d-20.grid").first
        grid.scroll_into_view_if_needed()
        if sh: sh.capture(grid, "verify_遊戲卡片區塊")
        if sh: sh.full_page("verify_遊戲卡片區塊_全頁")
        expect(grid).to_be_visible()

    def test_new_games_section(self, class_logged_in_page: Page, go_home):
        """RE-TC-017：首頁顯示「最新遊戲」區塊且有遊戲卡片"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        tab = page.locator("text=最新遊戲").first
        tab.scroll_into_view_if_needed()
        if sh: sh.capture(tab, "click_最新遊戲Tab")
        tab.click()
        grid = page.locator(".mt-d-20.grid").first
        # tab 切換後 grid 重繪，用 evaluate 捲動視窗避免操作 detached element
        page.evaluate("window.scrollBy(0, 400)")
        if sh: sh.capture(grid, "verify_最新遊戲卡片區塊")
        if sh: sh.full_page("verify_最新遊戲卡片區塊_全頁")
        expect(grid).to_be_visible()

    def test_announcement_marquee(self, class_logged_in_page: Page, go_home):
        """RE-TC-018：首頁公告跑馬燈有內容顯示"""
        page = class_logged_in_page
        marquee = page.locator("p.h-full").first
        sh = get_screenshotter(page)
        if sh: sh.capture(marquee, "verify_公告跑馬燈有內容")
        expect(marquee).to_be_visible()
        expect(marquee).to_contain_text("公告")

    def test_balance_visible(self, class_logged_in_page: Page, go_home):
        """RE-TC-019：登入後右上角餘額數字顯示（非空白）

        斷言策略：只驗 navbar 餘額欄位非空字串，不寫死特定數值。
        截圖 label 帶 balance_text 僅供 review 對照，非 expected 比對。
        """
        page = class_logged_in_page
        # 用容器而非 span：餘額為小數時會被拆成「整數」+「.小數」兩個 span
        balance = page.locator(".coin-wrap-bg")
        expect(balance).to_be_visible()
        balance_text = (balance.text_content() or "").strip()
        sh = get_screenshotter(page)
        if sh: sh.capture(balance, f"verify_navbar餘額非空_{balance_text}")
        assert balance_text != "", "餘額欄位不應為空字串"
