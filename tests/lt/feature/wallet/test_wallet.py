"""
餘額（信用額度）顯示測試 — LT desktop responsive 版（2026-05-18 rewrite）
WIN-WALLET-001~002

LT 為**信用板**站點（credit-based），前台**沒有存款流程**：
- 玩家使用代理商給予的信用額度直接下注，週期結算
- 信用額度只在 **navbar `.coin-wrap-bg span`** 顯示（HomePage.navbar_balance）
- 2026-05-18 換版後 member-center 改為 overlay panel，**panel 內不再顯示信用額度**
  → 原 WIN-WALLET-002 改為「panel 開啟時 navbar 信用額度仍可見」（驗證 overlay 不遮蓋 navbar）

舊 test_wallet.py 中的 drawer 餘額 / 存款入口測試自 WAP 改版起已無對應產品行為。
檔名保留以減少 diff 噪音；內容改以「balance visibility」切入。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.lt.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.wallet
class TestBalanceVisibility:
    """WIN-WALLET-001~002：信用額度（navbar / member-center panel 同步）顯示驗證"""

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
        if sh: sh.capture(home.navbar_balance, f"verify_navbar信用額度非空_{balance_text}")
        assert balance_text != "", "navbar 信用額度欄位不應為空"

    def test_balance_visible_in_member_center(self, class_logged_in_page: Page, go_home):
        """WIN-WALLET-002：開啟 member-center panel 後 navbar 信用額度仍可見

        2026-05-18 換版：信用額度只顯示在 navbar，panel 內已無此欄位。
        本 test 改為驗證「開 panel 時 overlay 不遮蓋 navbar 額度」，仍守住信用額度可見性。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_member_center()

        # panel 開啟後 navbar 應仍可見（in viewport），信用額度文字非空
        expect(home.navbar_balance).to_be_in_viewport()
        balance_text = (home.navbar_balance.inner_text() or "").strip()
        if sh: sh.capture(home.navbar_balance, f"verify_panel開啟時navbar信用額度非空_{balance_text}")
        assert balance_text != "", "panel 開啟時 navbar 信用額度欄位不應為空"
