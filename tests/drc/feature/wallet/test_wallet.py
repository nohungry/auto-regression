"""
錢包功能測試
"""

import pytest
from playwright.sync_api import Page, expect


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
