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
