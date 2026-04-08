"""
公開頁延伸功能測試
WIN-PUB-004~006, 010~011
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.dlt.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.dlt
class TestPublicFeatures:
    """WIN-PUB-004~006, 010~011：公開頁延伸功能"""

    def test_customer_service_visible(self, page: Page, site_config):
        """WIN-PUB-004：客服入口顯示"""
        login = LoginPage(page, site_config.url)
        login.goto()
        el = page.get_by_text("24小時客服").first
        expect(el).to_be_visible()
        sh = get_screenshotter(page)
        if sh: sh.capture(el, "verify_客服入口")

    def test_language_icon_visible(self, page: Page, site_config):
        """WIN-PUB-005：語系切換 icon 存在"""
        login = LoginPage(page, site_config.url)
        login.goto()
        el = page.locator('img[alt="Language"]').first
        expect(el).to_be_visible()
        sh = get_screenshotter(page)
        if sh: sh.capture(el, "verify_語系icon")

    def test_copyright_visible(self, page: Page, site_config):
        """WIN-PUB-006：版權資訊顯示"""
        login = LoginPage(page, site_config.url)
        login.goto()
        el = page.get_by_text("Copyright © 2025 LaiCai All rights reserved.").first
        expect(el).to_be_visible()
        sh = get_screenshotter(page)
        if sh: sh.capture(el, "verify_版權資訊")

    def test_customer_service_link_is_linee(self, page: Page, site_config):
        """WIN-PUB-010：客服連結指向 lin.ee"""
        login = LoginPage(page, site_config.url)
        login.goto()
        link = page.get_by_role("link", name="24小時客服").first
        expect(link).to_have_attribute("href", re.compile(r"lin\.ee"))
        sh = get_screenshotter(page)
        if sh: sh.capture(link, "verify_客服連結lin.ee")

    def test_browse_without_login_returns_home(self, page: Page, site_config):
        """WIN-PUB-011：登入頁「先去逛逛」可回首頁"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)

        browse_btn = page.get_by_role("button", name="先去逛逛")
        browse_btn.scroll_into_view_if_needed()
        if sh: sh.capture(browse_btn, "click_先去逛逛")
        browse_btn.click()

        expect(page).to_have_url(
            re.compile(r"^" + re.escape(site_config.url.rstrip("/")) + r"/?$"),
            timeout=5000,
        )
        expect(page.get_by_text("熱門", exact=True).first).to_be_visible()
        if sh: sh.full_page("verify_回到首頁")
