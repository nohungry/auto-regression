"""
RE 錢包功能測試 (BeWin) — navbar 餘額顯示區
RE-WALLET-001~002

注意：RE dev 環境前端無存款入口（依用戶指示，後台存錢/提取暫時不納入測試），
故僅驗證 navbar 餘額顯示區的 UI 完整性。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.re
class TestWallet:
    """
    RE-WALLET-001~002：navbar 餘額顯示區 UI 驗證
    class 內共用 session，不重複登入/登出。
    """

    def test_balance_displayed(self, class_logged_in_page: Page, go_home):
        """RE-WALLET-001：登入後 navbar 餘額數字可見（非空字串）

        斷言策略：只驗 navbar 餘額欄位非空字串，不寫死特定數值。
        截圖 label 帶 balance_text 僅供 review 對照，非 expected 比對。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)
        # 用容器而非 span：餘額為小數時會被拆成「整數」+「.小數」兩個 span
        balance = page.locator(".coin-wrap-bg")
        expect(balance).to_be_visible()
        balance_text = (balance.text_content() or "").strip()
        if sh: sh.capture(balance, f"verify_navbar餘額非空_{balance_text}")
        assert balance_text != "", "餘額欄位不應為空字串"

    @pytest.mark.skip(reason="RE 站 navbar 餘額區未實作獨立 refresh 按鈕（實機驗證 .coin-wrap-bg 內僅有 coin icon + 數字 span）")
    def test_balance_refresh_button_visible(self, class_logged_in_page: Page, go_home):
        """RE-WALLET-002：navbar 餘額區的重新整理按鈕可見

        [2026-04-29 實機驗證] RE 站 .coin-wrap-bg 結構為 coin.svg + span 餘額，
        無獨立 refresh 按鈕，與 RC 不同。skip 等待產品確認 RE 是否需要此功能。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)
        refresh_btn = page.locator(".coin-wrap-bg img[alt='refresh']")
        if sh: sh.capture(refresh_btn, "verify_餘額重新整理按鈕")
        expect(refresh_btn).to_be_visible()
