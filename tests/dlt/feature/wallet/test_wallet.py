"""
錢包功能測試（餘額 / 存款入口）
WIN-WALLET-001~003
"""

import pytest
from playwright.sync_api import Page, expect
from pages.dlt.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.wallet
class TestWallet:
    """WIN-WALLET-001~003：餘額顯示與存款入口驗證"""

    def test_balance_visible_in_navbar(self, class_logged_in_page: Page, go_home):
        """WIN-WALLET-001：登入後導覽列顯示餘額數字（非空字串）"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        # 導覽列有 mobile/desktop 兩個 p.text-amount，mobile 在 desktop 下隱藏
        # nth(0)=mobile(hidden)，nth(1)=desktop(visible)
        balance = page.locator("p.text-amount").nth(1)
        expect(balance).to_be_visible()
        balance_text = balance.text_content() or ""
        assert balance_text.strip() != "", "導覽列餘額欄位不應為空"
        if sh: sh.capture(balance, "verify_導覽列餘額")

    def test_balance_visible_in_drawer(self, class_logged_in_page: Page, go_home):
        """WIN-WALLET-002：開啟會員 drawer 後顯示餘額"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.open_member_drawer()
        balance = page.locator("p.font-bold.text-amount")
        expect(balance).to_be_visible()
        if sh: sh.capture(balance, "verify_drawer餘額")

    def test_deposit_entry_opens_dialog(self, class_logged_in_page: Page, go_home):
        """WIN-WALLET-003：存款/維護時間入口可點擊，點擊後開啟對話框"""
        page = class_logged_in_page
        home = HomePage(page)
        home.open_deposit_dialog()
        expect(page.locator(".dialog-mask")).to_be_visible()
        home.close_dialog()
