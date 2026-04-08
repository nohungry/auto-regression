"""
登入後功能測試
WIN-AUTH-002, 004
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.dlt.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.login
class TestAuthFeatures:
    """WIN-AUTH-002, 004：登入後功能驗證"""

    def test_member_features_text_visible(self, logged_in_page: Page):
        """WIN-AUTH-002：登入後會員功能文案存在（投注紀錄/會員訊息/維護時間/登出）"""
        home = HomePage(logged_in_page)
        home.open_member_drawer()
        sh = get_screenshotter(logged_in_page)
        for text in ["投注紀錄", "會員訊息", "維護時間", "登出"]:
            el = logged_in_page.get_by_text(text).first
            expect(el).to_be_visible()
            if sh: sh.capture(el, f"verify_會員功能_{text}")

    def test_category_navigation_after_login(self, logged_in_page: Page, site_config):
        """WIN-AUTH-004：登入後可切換真人與電子頁，帳號名稱仍顯示"""
        home = HomePage(logged_in_page)
        sh = get_screenshotter(logged_in_page)
        for label, url_pattern in [("真人", re.compile(r"/Categories/casino")),
                                    ("電子", re.compile(r"/Categories/slots"))]:
            home.click_nav_item(label)
            expect(logged_in_page).to_have_url(url_pattern, timeout=8000)
            username_el = logged_in_page.locator(
                '[class*="font-medium"]', has_text=site_config.username
            ).first
            expect(username_el).to_be_visible()
            if sh: sh.capture(username_el, f"verify_帳號顯示_{label}頁")
