"""
KS 錢包功能測試（Super9娛樂城）
KS-WALLET-001 ~ 003

驗證 nav wallet 圖示顯示 + 儲值/提領入口導航（/member-center?type=Deposit / Withdrawal）。
probe 2026-06-06：KS 用 nav wallet 圖示（img[alt='Wallet']）作已登入/錢包信號。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("ks")


@pytest.mark.p1
@pytest.mark.ks
@pytest.mark.wallet
class TestWallet:
    """KS-WALLET-001 ~ 003：錢包圖示 + 儲值/提領入口"""

    def test_wallet_indicator_displayed(self, class_logged_in_page: Page, go_home):
        """KS-WALLET-001：nav wallet 圖示登入後可見"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        expect(home.wallet_indicator).to_be_visible(timeout=10000)
        home.wallet_indicator.scroll_into_view_if_needed()
        if sh: sh.capture(home.wallet_indicator, "verify_wallet圖示")

    @pytest.mark.parametrize("type_key", ["Deposit", "Withdrawal"])
    def test_wallet_link_navigates(self, class_logged_in_page: Page, go_home, type_key):
        """KS-WALLET-00x：drawer 點儲值/提領後 URL 帶 type=<key>"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_member_link(type_key)

        page.wait_for_url(lambda url: f"type={type_key}" in url, timeout=8000)
        assert "/member-center" in page.url, f"預期進 member-center，實際 {page.url}"
        if sh: sh.full_page(f"verify_wallet_{type_key}")
