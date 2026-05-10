"""
RD 錢包功能測試（總資產顯示）— 狗狗娛樂城
RD-WALLET-001 ~ 002

與 RC 差異：
- RD navbar **不顯示**餘額，需點「個人資訊」icon 開啟面板才能看到
- 面板內以「總資產」label + 金額數值顯示
- RD **無**餘額重新整理按鈕（RC 有 `.coin-wrap-bg img[alt='refresh']`）

故 RD wallet 只測 panel 內的「總資產 label + 數值非空」2 項。
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("rd")


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.wallet
class TestWallet:
    """
    RD-WALLET-001 ~ 002：個人資訊面板內「總資產」顯示驗證

    每個 test 透過 home.open_user_dropdown() 開啟面板再驗證；class 內共用 session。
    """

    def test_total_assets_label_visible(self, class_logged_in_page: Page, go_home):
        """RD-WALLET-001：個人資訊面板顯示「總資產」label"""
        page = class_logged_in_page
        sh = get_screenshotter(page)

        home = HomePage(page)
        home.open_user_dropdown()

        label = page.locator("div.dialog-mask p, div.dialog-mask span", has_text="總資產").first
        expect(label).to_be_visible(timeout=5000)
        if sh: sh.capture(label, "verify_總資產label")

    def test_balance_value_displayed(self, class_logged_in_page: Page, go_home):
        """RD-WALLET-002：「總資產」金額數值顯示且非空（不寫死特定數值，只驗格式）

        斷言策略：只驗數值符合金錢格式（含千分位/小數），不寫死帳戶餘額；
        截圖 label 帶實際數值僅供 review，非比對 expected。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)

        home = HomePage(page)
        home.open_user_dropdown()

        # 「總資產」下方 span 為金額數值，class 為 truncate font-bold text-white，
        # 父層 div.flex.flex-col.overflow-hidden.text-[20px]
        balance = page.locator(
            "div.dialog-mask div.flex.flex-col.overflow-hidden span.truncate.font-bold"
        ).first
        expect(balance).to_be_visible(timeout=5000)

        balance_text = (balance.text_content() or "").strip()
        if sh: sh.capture(balance, f"verify_總資產數值非空_格式_{balance_text}")

        # 格式驗證：數字 + 可選千分位 + 可選小數（如 "1,000.00" / "0" / "12345.6"）
        assert balance_text != "", "總資產數值不應為空"
        assert re.match(r"^-?[\d,]+(\.\d+)?$", balance_text), (
            f"總資產數值格式不符（金錢格式期望 \\d+(,\\d+)*(\\.\\d+)?）：實際 '{balance_text}'"
        )
