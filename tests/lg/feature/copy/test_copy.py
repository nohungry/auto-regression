"""
LG 文案一致性驗證（大撈家娛樂城）
LG-TC-C01 ~ LG-TC-C02

驗證 LG 站「預設語系（繁中）」下的品牌/導覽文案資產（probe 2026-06-07）：
- 網站標題（品牌 + slogan）
- 頂部 nav 主分類顯示文字與順序（ul.nav-item li）

只驗未登入公開頁可見的文案；多語系切換驗證見 tests/lg/feature/i18n/。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lg")

# 頂部 nav 顯示文字（ul.nav-item li，含遊戲分類 + 優惠/公告）
EXPECTED_NAV_LABELS = [
    "熱門", "電子", "真人", "捕魚", "棋牌", "體育", "彩票", "鬥雞", "優惠", "公告",
]


@pytest.mark.p2
@pytest.mark.lg
@pytest.mark.copy
class TestCopy:
    """LG 文案一致性驗證（未登入公開頁）"""

    def test_home_title(self, page: Page, site_config):
        """LG-TC-C01：首頁網站標題為品牌 + slogan"""
        LoginPage(page, site_config.url).goto()
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_首頁title_{page.title()}")
        expect(page).to_have_title("大撈家娛樂城 - 領先的在線娛樂遊戲體驗")

    def test_nav_labels(self, page: Page, site_config):
        """LG-TC-C02：頂部 nav 主分類顯示文字與順序正確（繁中）"""
        LoginPage(page, site_config.url).goto()
        labels = page.locator("ul.nav-item li").evaluate_all(
            "els => els.map(li => (li.textContent || '').trim())"
        )
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_nav文案_{labels}")
        assert labels == EXPECTED_NAV_LABELS, f"nav 文案不符，實際：{labels}"
