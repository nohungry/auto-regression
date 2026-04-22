"""
餘額（信用額度）顯示測試 — LT WAP 版（2026-04-22 rewrite）
WIN-WALLET-001~002

LT 為**信用板**站點（credit-based），前台**沒有存款流程**：
- 玩家使用代理商給予的信用額度直接下注，週期結算。
- navbar / /member-center 顯示的是**信用額度**，不是「可提領錢包餘額」。
- 舊 test_wallet.py 中的 drawer 餘額 / 存款入口測試已無對應產品行為（drawer 消失、存款流程不存在）。

本檔只守門「餘額/信用額度在兩個位置顯示非空文字」：
- WIN-WALLET-001：navbar 的 `.bg-navbar p.text-amount` 顯示非空數字
- WIN-WALLET-002：/member-center 的 `p.font-bold.text-amount` 顯示非空數字

檔名保留 `test_wallet.py` 以減少 diff 噪音；內容改以「balance visibility」切入。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.lt.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.wallet
class TestBalanceVisibility:
    """WIN-WALLET-001~002：信用額度（navbar / member-center）顯示驗證"""

    def test_balance_visible_in_navbar(self, class_logged_in_page: Page, go_home):
        """WIN-WALLET-001：首頁 navbar 顯示非空信用額度

        斷言策略：信用額度會隨投注結算變動，**只驗非空**（`!= ""`），不寫死特定數值；
        截圖 label 帶當前值（`verify_navbar信用額度非空_XXX`）僅供人工 review，不構成斷言比對。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        expect(home.navbar_balance).to_be_in_viewport()
        balance_text = (home.navbar_balance.inner_text() or "").strip()
        assert balance_text != "", "navbar 信用額度欄位不應為空"
        if sh: sh.capture(home.navbar_balance, f"verify_navbar信用額度非空_{balance_text}")

    def test_balance_visible_in_member_center(self, class_logged_in_page: Page, go_home):
        """WIN-WALLET-002：/member-center 顯示非空信用額度

        斷言策略：同 WIN-WALLET-001，只驗非空，不寫死值；label 帶值僅供 review。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_member_center()

        balance = page.locator("p.font-bold.text-amount").first
        balance.scroll_into_view_if_needed()
        expect(balance).to_be_visible()
        balance_text = (balance.inner_text() or "").strip()
        assert balance_text != "", "member-center 信用額度欄位不應為空"
        if sh: sh.capture(balance, f"verify_member_center信用額度非空_{balance_text}")
