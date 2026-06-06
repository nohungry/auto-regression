"""
KS 文案一致性驗證（Super9娛樂城）
KS-TC-C01 ~ KS-TC-C02

驗證 KS 站「預設語系（简体）」下的品牌/導覽文案資產（probe 2026-06-07）：
- 網站標題（注意：title 為繁体「Super9娛樂城」，UI 主體為简体）
- 頂部 nav 主分類顯示文字與順序（ul.nav-item li，简体）

只驗未登入公開頁可見的文案；多語系切換驗證見 tests/ks/feature/i18n/。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("ks")

# 頂部 nav 顯示文字（ul.nav-item li，简体；含遊戲分類 + 优惠活动）
EXPECTED_NAV_LABELS = [
    "电子", "真人", "体育", "捕鱼", "小游戏", "彩票", "优惠活动",
]


@pytest.mark.p2
@pytest.mark.ks
@pytest.mark.copy
class TestCopy:
    """KS 文案一致性驗證（未登入公開頁）"""

    def test_home_title(self, page: Page, site_config):
        """KS-TC-C01：首頁網站標題為品牌 + slogan（title 為繁体）"""
        LoginPage(page, site_config.url).goto()
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_首頁title_{page.title()}")
        expect(page).to_have_title("Super9娛樂城 - 領先的在線娛樂遊戲體驗")

    def test_nav_labels(self, page: Page, site_config):
        """KS-TC-C02：頂部 nav 主分類顯示文字與順序正確（简体）"""
        LoginPage(page, site_config.url).goto()
        labels = page.locator("ul.nav-item li").evaluate_all(
            "els => els.map(li => (li.textContent || '').trim())"
        )
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_nav文案_{labels}")
        assert labels == EXPECTED_NAV_LABELS, f"nav 文案不符，實際：{labels}"
