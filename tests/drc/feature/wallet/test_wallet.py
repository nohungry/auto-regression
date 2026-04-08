"""
錢包功能測試（餘額顯示區）
DRC-WALLET-001~002

注意：DRC dev 環境無存款入口（存款為後端功能，不在前端 UI 呈現），
故僅驗證 navbar 餘額顯示區的 UI 完整性。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
class TestWallet:
    """
    DRC-WALLET-001~002：navbar 餘額顯示區 UI 驗證
    class 內共用 session，不重複登入/登出。
    """

    def test_balance_displayed(self, class_logged_in_page: Page, go_home):
        """DRC-WALLET-001：登入後 navbar 餘額數字可見（非空字串）"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        balance = page.locator(".coin-wrap-bg span")
        expect(balance).to_be_visible()
        balance_text = balance.text_content() or ""
        assert balance_text.strip() != "", "餘額欄位不應為空字串"
        if sh: sh.capture(balance, "verify_navbar餘額數字")

    def test_balance_refresh_button_visible(self, class_logged_in_page: Page, go_home):
        """DRC-WALLET-002：navbar 餘額區的重新整理按鈕可見"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        refresh_btn = page.locator(".coin-wrap-bg img[alt='refresh']")
        expect(refresh_btn).to_be_visible()
        if sh: sh.capture(refresh_btn, "verify_餘額重新整理按鈕")
