"""
LU 錢包功能測試（Dlgbet）
LU-WALLET-001 ~ 007

probe 2026-06-06：LU nav 餘額 span 顯示（登入後）。存款/提現為 sidebar in-panel JS
handler（非 URL 導航），故錢包層僅驗餘額顯示。
probe 2026-08-10：錢包 dialog 容器 class 改版（max-w-[612px] → lg:max-w-[600px]，
POM 已追平），並補齊 dialog 內部金流結構驗證（存款/提現分頁、付款平台格線、送出鈕）。
LU 未綁銀行卡也能進存款頁（對照 LG/QW 有「請先綁定銀行卡」守衛，見該兩站 wallet 測試）。

覆蓋邊界：一律**不送出**存款單——送出會產生無法對稱回復的金流紀錄（D-015）。
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

    def test_deposit_entry_opens_dialog(self, class_logged_in_page: Page, go_home):
        """LU-WALLET-003：頂部 nav 儲值 + 開啟錢包 dialog（probe 2026-07-24）

        斷言策略：dispatch_event 點擊（LU 殘留 dialog-mask 站慣例）→
        錢包 dialog 可見、URL 停留首頁。
        空帳號站：只驗入口與 dialog 開啟，不做真實存款。
        """
        page = class_logged_in_page
        home = HomePage(page)
        home.open_deposit_dialog()
        expect(home.wallet_dialog).to_be_visible()
        assert "/member" not in page.url, f"錢包 dialog 應為 in-page modal，實際 URL：{page.url}"

    def test_withdraw_entry_opens_dialog(self, class_logged_in_page: Page, go_home):
        """LU-WALLET-004：頂部 nav 提現 button 開啟錢包 dialog（probe 2026-07-24）

        斷言策略同 LU-WALLET-003；提現與儲值共用同一個錢包 dialog 容器。
        """
        page = class_logged_in_page
        home = HomePage(page)
        home.open_withdraw_dialog()
        expect(home.wallet_dialog).to_be_visible()

    def test_deposit_dialog_has_wallet_tabs(self, class_logged_in_page: Page, go_home):
        """LU-WALLET-005：錢包 dialog 內含「存款 / 提現」兩個分頁（probe 2026-08-10）

        存提共用同一容器、以分頁切換 → 分頁存在是「金流入口完整」的結構性訊號。
        斷言分頁文字集合而非順序以外的細節；LU 為實質單語系顯示（後台/前台皆固定中文），
        文字定位風險已評估。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_deposit_dialog()
        tabs = home.wallet_tab_texts()
        if sh: sh.capture(home.wallet_dialog, f"verify_錢包分頁_{'_'.join(tabs)}")
        assert tabs == ["存款", "提現"], f"錢包 dialog 分頁與預期不符：{tabs}"

    def test_deposit_dialog_lists_payment_platforms(self, class_logged_in_page: Page, go_home):
        """LU-WALLET-006：存款分頁列出可用付款平台（probe 2026-08-10）

        金流覆蓋從「入口能開」推進到「存款頁真的有可用渠道」：付款平台格線非空，
        且每格皆有非空顯示文字（空白格＝渠道設定壞掉，是要回報的訊號）。
        不斷言特定平台名稱與數量——渠道由後台設定，會隨營運調整。
        不送出：帳號層級只驗渠道呈現，不產生真實存款單。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_deposit_dialog()
        platforms = home.payment_platform_texts()
        if sh: sh.capture(home.payment_platform_grid, f"verify_付款平台清單_{len(platforms)}項")

        assert platforms, "存款分頁付款平台格線為空（無可用渠道）"
        blank = [i for i, t in enumerate(platforms) if not t]
        assert not blank, f"付款平台有空白格（index={blank}）：{platforms}"

    def test_deposit_dialog_has_submit_button(self, class_logged_in_page: Page, go_home):
        """LU-WALLET-007：存款分頁底部送出鈕存在且可用（probe 2026-08-10）

        只驗按鈕呈現與 enabled 狀態，**不點擊**——點擊會產生真實存款單，
        無法對稱回復（D-015 可逆要求）。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_deposit_dialog()
        expect(home.wallet_submit_btn).to_be_visible(timeout=8000)
        expect(home.wallet_submit_btn).to_be_enabled()
        if sh: sh.capture(home.wallet_submit_btn, "verify_存款送出鈕")
