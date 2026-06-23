"""
RF 錢包功能測試（金爺娛樂城，信用版）
RF-WALLET-001 ~ 002

probe 結果（dev-rf，2026-06-17）：
- 首頁 navbar 餘額：.loginInBox .coin span（text: 如 10,000.00）
  / .loginInBox .coin img[alt="Coin"]（金幣圖示）。
- 帳戶設定 modal 內總資產：.account-settings__balance（text nodes，排除 SVG）。
- 信用版無真實存提功能：dropmenu 無「錢包管理/儲值/提領」入口，
  探查顯示全頁「錢包管理」count=0，不適用存提測試。
- 所有操作均唯讀，不改動後端狀態。

斷言策略：
- 餘額驗「非空」且「格式含數字」，不寫死特定金額（帳號餘額可能因測試資料變動）。
- screenshot label 帶「非空」標記，避免 reviewer 誤以為是寫死比對。
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("rf")

# 信用版餘額格式正規表示式（數字 + 逗號 + 小數點，如 10,000.00 / 0.00）
_BALANCE_PATTERN = re.compile(r"[\d,]+\.\d{2}")


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.wallet
class TestWallet:
    """RF-WALLET-001 ~ 002：信用額度顯示唯讀驗證"""

    def test_navbar_balance_displayed(self, class_logged_in_page: Page, go_home):
        """RF-WALLET-001：登入後首頁 navbar .loginInBox .coin span 顯示信用額度（非空 + 數字格式）。

        斷言策略：
        - .coin span 可見（已登入信號之一）。
        - 文字非空且符合餘額格式（數字+逗號+小數點），不寫死金額。
        - .coin img[alt="Coin"] 可見（金幣圖示，UI 完整性確認）。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        # 截圖在 assertion 前
        balance_text = home.get_navbar_balance_text()

        # 金幣圖示可見
        coin_img = home.account_box.locator("img[alt='Coin']")
        expect(coin_img).to_be_visible(timeout=5000)
        coin_img.scroll_into_view_if_needed()
        if sh:
            sh.capture(coin_img, f"verify_金幣圖示可見_pre_assert")

        # 斷言
        assert balance_text, f"信用額度不應為空，實際: {repr(balance_text)}"
        assert _BALANCE_PATTERN.search(balance_text), (
            f"信用額度格式應含數字（如 10,000.00），實際: {repr(balance_text)}"
        )

        if sh:
            sh.full_page(f"verify_navbar信用額度非空_{balance_text}")

    def test_modal_balance_matches_navbar(self, class_logged_in_page: Page, go_home):
        """RF-WALLET-002：帳戶設定 modal 內「總資產」金額與首頁 navbar 顯示一致。

        斷言策略：
        - 兩處均非空 + 格式正確。
        - 驗兩處數值相同（排除時間差造成的極小誤差，此站信用版額度不會在測試期間變動）。
        - 唯讀操作；開啟 modal 後關閉還原狀態。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        # 先取 navbar 餘額（modal 開啟前）
        navbar_balance = home.get_navbar_balance_text()
        assert navbar_balance, f"navbar 信用額度不應為空，實際: {repr(navbar_balance)}"
        if sh:
            sh.full_page(f"verify_navbar信用額度非空_{navbar_balance}_pre_open_modal")

        # 開啟帳戶設定 modal
        home.open_account_settings()

        # 取 modal 內總資產
        modal_balance = home.get_modal_balance_text()

        # modal 餘額截圖（截圖在 assert 前）；selector 對齊 POM get_modal_balance_text 讀取的 .account-settings__balance
        asset_el = page.locator(".account-settings__balance").first
        asset_el.scroll_into_view_if_needed()
        if sh:
            sh.capture(asset_el, f"verify_modal總資產非空_{modal_balance}_pre_assert")

        # 斷言
        assert modal_balance, f"modal 總資產不應為空，實際: {repr(modal_balance)}"
        assert _BALANCE_PATTERN.search(modal_balance), (
            f"modal 總資產格式應含數字，實際: {repr(modal_balance)}"
        )
        assert navbar_balance == modal_balance, (
            f"navbar 餘額（{navbar_balance}）與 modal 總資產（{modal_balance}）應相同"
        )

        if sh:
            sh.full_page(f"verify_modal總資產與navbar一致_{modal_balance}")

        home.close_account_settings()
