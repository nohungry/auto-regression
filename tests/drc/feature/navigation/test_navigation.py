"""
導覽列功能測試
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.drc.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
class TestNavigation:
    """
    導覽列功能測試
    class 內共用 session，每個測試前由 go_home 回到首頁
    """

    def test_casino_page_loads(self, class_logged_in_page: Page, go_home):
        """點擊真人分類後頁面正常載入"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.click_nav_item("真人")
        expect(page).to_have_url(re.compile("Categories/casino"), timeout=8000)
        if sh: sh.full_page("verify_真人分類頁載入")

    def test_slots_page_loads(self, class_logged_in_page: Page, go_home):
        """點擊電子分類後頁面正常載入"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.click_nav_item("電子")
        expect(page).to_have_url(re.compile("Categories/slots"), timeout=8000)
        if sh: sh.full_page("verify_電子分類頁載入")

    def test_fishing_page_loads(self, class_logged_in_page: Page, go_home):
        """點擊捕魚分類後頁面正常載入"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.click_nav_item("捕魚")
        expect(page).to_have_url(re.compile("Categories/fishing"), timeout=8000)
        if sh: sh.full_page("verify_捕魚分類頁載入")

    def test_casino_halls_visible(self, class_logged_in_page: Page, go_home):
        """TC-015：真人頁顯示所有廳館（T9真人、RC真人、DG真人、MT真人、歐博）"""
        page = class_logged_in_page
        home = HomePage(page)
        home.click_nav_item("真人")
        sh = get_screenshotter(page)
        for hall in ["T9真人", "RC真人", "DG真人", "MT真人", "歐博"]:
            # sidebar 的廳館文字使用 text-black，排除後取廳館卡片內的可見節點
            el = page.locator("p:not(.text-black)", has_text=hall).first
            expect(el).to_be_visible(timeout=8000)
            el.scroll_into_view_if_needed()
            if sh: sh.capture(el, f"verify_廳館_{hall}")
        if sh: sh.full_page("verify_所有廳館卡片_全頁")
