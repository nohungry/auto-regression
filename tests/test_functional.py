"""
功能型測試（Functional Tests）
- 使用 class_logged_in_page：一個 class 只登入一次，class 內測試共用 session
- 使用 go_home：每個測試前自動回到首頁並清理彈窗
- 不測試登入/登出流程本身（那是 Smoke test 的範疇）

執行方式：
    .venv/bin/pytest tests/test_functional.py -v
    .venv/bin/pytest tests/test_functional.py -v -k "TestWallet"
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.home_page import HomePage


@pytest.mark.p1
class TestWallet:
    """
    錢包相關功能測試
    class 內所有測試共用同一個登入 session，不會重複登入/登出
    """

    def test_balance_displayed(self, class_logged_in_page: Page, go_home):
        """餘額顯示正常（非空白）"""
        page = class_logged_in_page
        expect(page.locator(".coin-wrap-bg span")).to_be_visible()

    def test_deposit_entry_visible(self, class_logged_in_page: Page, go_home):
        """存款入口可見（示範：驗證首頁存款按鈕存在）"""
        page = class_logged_in_page
        # TODO: 替換為實際的存款元素 selector
        expect(page.locator(".coin-wrap-bg")).to_be_visible()


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
