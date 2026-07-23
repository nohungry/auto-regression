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

    def test_balance_has_numeric_value(self, class_logged_in_page: Page, go_home):
        """LU-WALLET-002：nav 餘額 span 顯示非空且含數字

        延伸 LU-WALLET-001（僅驗可見）→ 驗餘額「有值」。模板參考 LG/KS test_balance_displayed。
        斷言策略：只驗餘額文字非空且至少含一位數字，不寫死特定金額（LU 為空帳號站，
        餘額可能為 0，但仍應為合法數值字串）；截圖 label 帶「非空含數字」+ 值僅供 review。
        selector 取自 LU HomePage.balance（.fixed.top-0.z-50 nav 餘額 span），未引入新 selector。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        expect(home.balance).to_be_visible(timeout=10000)
        home.balance.scroll_into_view_if_needed()
        text = home.balance.inner_text().strip()
        if sh: sh.capture(home.balance, f"verify_餘額非空含數字_{text}")
        assert text, "餘額文字為空"
        assert any(c.isdigit() for c in text), f"餘額文字不含數字：{text!r}"
