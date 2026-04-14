"""
錢包功能測試（餘額 / 存款入口）
WIN-WALLET-001~003
"""

import pytest
from playwright.sync_api import Page, expect
from pages.lt.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.wallet
class TestWallet:
    """WIN-WALLET-001~003：餘額顯示與存款入口驗證"""

    def test_balance_visible_in_navbar(self, class_logged_in_page: Page, go_home):
        """WIN-WALLET-001：登入後導覽列（桌機版）顯示餘額數字（非空字串）

        navbar 餘額位於右上角，x 座標與 drawer 滑入區重疊；若 drawer 開啟截圖會被遮擋，
        故先確保 drawer 關閉。Selector 以 `div[class*="lg:flex"] p.text-amount` 鎖定桌機版容器，
        避免與 drawer 內 `p.font-bold.text-amount` 混淆。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.close_drawer_if_open()
        expect(home.navbar_balance).to_be_in_viewport()
        balance_text = (home.navbar_balance.text_content() or "").strip()
        assert balance_text != "", "導覽列餘額欄位不應為空"
        if sh: sh.capture(home.navbar_balance, "verify_導覽列餘額")

    def test_balance_visible_in_drawer(self, class_logged_in_page: Page, go_home):
        """WIN-WALLET-002：開啟會員 drawer 後 drawer 餘額進入 viewport 且有非空文字

        drawer 容器（.fixed.bottom-0.right-0）用 CSS translate-x-full 滑出視窗，
        DOM 永遠存在 → `to_be_visible()` 永遠為真，無法偵測 drawer 有無真的滑入。
        改用 `to_be_in_viewport()` 確認 drawer 滑入後餘額才真的可見。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.open_member_drawer()
        balance = page.locator("p.font-bold.text-amount")
        expect(balance).to_be_in_viewport()
        balance_text = (balance.text_content() or "").strip()
        assert balance_text != "", "drawer 餘額欄位不應為空"
        if sh: sh.capture(balance, "verify_drawer餘額")

    def test_maintenance_time_entry_opens_dialog(self, class_logged_in_page: Page, go_home):
        """WIN-WALLET-003：維護時間入口可點擊，點擊後開啟對話框
        dev 站點目前存款功能關閉，該按鈕顯示為「維護時間」；存款功能開放時按鈕文案會改為「存款」。
        """
        page = class_logged_in_page
        home = HomePage(page)
        home.open_maintenance_time_dialog()
        expect(page.locator(".dialog-mask")).to_be_visible()
        home.close_dialog()
