"""
導覽列功能測試
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.drc.home_page import HomePage


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
        home.click_nav_item("真人")
        expect(page).to_have_url(re.compile("Categories/casino"), timeout=8000)

    def test_slots_page_loads(self, class_logged_in_page: Page, go_home):
        """點擊電子分類後頁面正常載入"""
        page = class_logged_in_page
        home = HomePage(page)
        home.click_nav_item("電子")
        expect(page).to_have_url(re.compile("Categories/slots"), timeout=8000)

    def test_fishing_page_loads(self, class_logged_in_page: Page, go_home):
        """點擊捕魚分類後頁面正常載入"""
        page = class_logged_in_page
        home = HomePage(page)
        home.click_nav_item("捕魚")
        expect(page).to_have_url(re.compile("Categories/fishing"), timeout=8000)
