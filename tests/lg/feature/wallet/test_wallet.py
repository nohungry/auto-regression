"""
LG 錢包功能測試（大撈家娛樂城）
LG-WALLET-001 ~ 003

驗證 nav 餘額顯示 + 儲值/提領入口導航（/member-center?type=Deposit / Withdrawal）。
probe 2026-06-06：nav .balance-color 顯示餘額；dropdown 有 儲值/提領 連結。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lg")


@pytest.mark.p1
@pytest.mark.lg
@pytest.mark.wallet
class TestWallet:
    """LG-WALLET-001 ~ 003：餘額顯示 + 儲值/提領入口"""

    def test_balance_displayed(self, class_logged_in_page: Page, go_home):
        """LG-WALLET-001：nav 餘額（.balance-color）登入後可見"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        expect(home.balance).to_be_visible(timeout=10000)
        home.balance.scroll_into_view_if_needed()
        if sh: sh.capture(home.balance, "verify_餘額顯示")

    @pytest.mark.parametrize("type_key", ["Deposit", "Withdrawal"])
    def test_wallet_link_navigates(self, class_logged_in_page: Page, go_home, type_key):
        """LG-WALLET-00x：dropdown 點儲值/提領後 URL 帶 type=<key>"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_member_link(type_key)

        page.wait_for_url(lambda url: f"type={type_key}" in url, timeout=8000)
        assert "/member-center" in page.url, f"預期進 member-center，實際 {page.url}"
        if sh: sh.full_page(f"verify_wallet_{type_key}")

    def test_deposit_entry_offers_next_step(self, class_logged_in_page: Page, go_home):
        """LG-WALLET-004：點儲值入口後，頁面提供明確可操作的下一步（probe 2026-08-10）

        test_wallet_link_navigates[Deposit] 只驗「URL 瞬間帶 type=Deposit」——實測那之後
        約 1 秒，未綁銀行卡的帳號會被提示「請先綁定銀行卡」並導向 type=Withdrawal 的
        銀行卡管理區。該條綠燈因此不代表儲值頁真的可用，本條補上「最終落點可操作」這層。

        斷言策略：不斷言瞬時提示（生命週期約 1 秒，硬等會 flaky），改等最終落點的可操作
        元素——「新增銀行卡」入口可見。同時守住 bug #11 那類「錯誤不渲染、留白頁無下一步」
        的缺陷（LG 已有前科）。

        ⚠️ 現況綁定：本條反映「測試帳號未綁卡」的守衛路徑。若日後帳號綁了銀行卡，
        儲值頁不再被導走，本條會 fail —— 屆時應重新 probe 儲值渠道 DOM，改驗渠道呈現
        （LU 已有該路徑的模板：LU-WALLET-006）。fail 即為測試資料變更的訊號，不是誤報。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_member_link("Deposit")

        add_bank_btn = page.get_by_text("新增銀行卡", exact=False).first
        expect(add_bank_btn).to_be_visible(timeout=15000)
        if sh: sh.capture(add_bank_btn, "verify_儲值守衛_導向綁卡入口")

        assert "/member-center" in page.url, f"預期停在會員中心，實際 URL：{page.url}"
