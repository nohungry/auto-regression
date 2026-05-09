"""
RD 導覽列功能測試 (狗狗娛樂城)

驗證 6 個主分類點擊後 URL 正確跳轉：
- 真人 → /Categories/casino
- 電子 → /Categories/slots
- 捕魚 → /Categories/fishing
- 體育 → /Categories/sport
- 彩票 → /Categories/lottery
- 鬥雞 → /Categories/cockfighting

對照 RC（5 類）/ RE（5 類含鬥雞，URL 為 /cock）有差異：
- RD 體育是 `sport`（單數），RE 是 `sports`
- RD 鬥雞是 `cockfighting`（完整字），RE 是 `cock`
- RD 獨有「彩票」分類
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("rd")


@pytest.mark.p1
@pytest.mark.rd
class TestNavigation:
    """RD 導覽列點擊跳轉驗證

    使用 class_logged_in_page + go_home：每個 test 前回首頁並關掉公告蓋板。
    """

    def test_casino_page_loads(self, class_logged_in_page: Page, go_home):
        """RD-TC-N01：點擊真人分類後跳轉至 /Categories/casino"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.click_nav_item("真人")
        if sh: sh.full_page("verify_真人分類頁載入")
        expect(page).to_have_url(re.compile("Categories/casino"), timeout=8000)

    def test_slots_page_loads(self, class_logged_in_page: Page, go_home):
        """RD-TC-N02：點擊電子分類後跳轉至 /Categories/slots"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.click_nav_item("電子")
        if sh: sh.full_page("verify_電子分類頁載入")
        expect(page).to_have_url(re.compile("Categories/slots"), timeout=8000)

    def test_fishing_page_loads(self, class_logged_in_page: Page, go_home):
        """RD-TC-N03：點擊捕魚分類後跳轉至 /Categories/fishing"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.click_nav_item("捕魚")
        if sh: sh.full_page("verify_捕魚分類頁載入")
        expect(page).to_have_url(re.compile("Categories/fishing"), timeout=8000)

    def test_sport_page_loads(self, class_logged_in_page: Page, go_home):
        """RD-TC-N04：點擊體育分類後跳轉至 /Categories/sport（RD 為單數）"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.click_nav_item("體育")
        if sh: sh.full_page("verify_體育分類頁載入")
        expect(page).to_have_url(re.compile(r"Categories/sport(?!s)"), timeout=8000)

    def test_lottery_page_loads(self, class_logged_in_page: Page, go_home):
        """RD-TC-N05：點擊彩票分類後跳轉至 /Categories/lottery（RD 獨有）"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.click_nav_item("彩票")
        if sh: sh.full_page("verify_彩票分類頁載入")
        expect(page).to_have_url(re.compile("Categories/lottery"), timeout=8000)

    def test_cockfighting_page_loads(self, class_logged_in_page: Page, go_home):
        """RD-TC-N06：點擊鬥雞分類後跳轉至 /Categories/cockfighting

        注意：RD 為完整字 `cockfighting`，RE 站為縮寫 `cock`。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.click_nav_item("鬥雞")
        if sh: sh.full_page("verify_鬥雞分類頁載入")
        expect(page).to_have_url(re.compile("Categories/cockfighting"), timeout=8000)
