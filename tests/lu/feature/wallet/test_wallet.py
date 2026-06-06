"""
LU 錢包功能測試（Dlgbet）
LU-WALLET-001

probe 2026-06-06：LU nav 餘額 span 顯示（登入後）。存款/提現為 sidebar in-panel JS
handler（非 URL 導航），故錢包層僅驗餘額顯示；存提流程留待後續波（需 probe in-panel UI）。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lu")


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.wallet
class TestWallet:
    """LU-WALLET-001：餘額顯示"""

    def test_balance_displayed(self, class_logged_in_page: Page, go_home):
        """LU-WALLET-001：nav 餘額 span 登入後可見"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        expect(home.balance).to_be_visible(timeout=10000)
        home.balance.scroll_into_view_if_needed()
        if sh: sh.capture(home.balance, "verify_餘額顯示")
