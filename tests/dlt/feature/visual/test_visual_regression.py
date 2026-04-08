"""
視覺截圖存檔（p2，供人工目視確認）
WIN-VR-001~003

截圖存於 screenshots/dlt/vr_reference/，不做 pixel 比對。
因各人螢幕解析度不同，pixel-level baseline 比對無法跨環境穩定運作。
"""

import pytest
from playwright.sync_api import Page
from pages.dlt.login_page import LoginPage
from tests.dlt.feature.visual.helpers import BANNER_SELECTORS, save_screenshot, screenshot_with_mask


@pytest.mark.p2
@pytest.mark.dlt
@pytest.mark.visual_regression
class TestVisualRegression:
    """WIN-VR-001~003：截圖存檔供人工目視確認（不做 baseline 比對）"""

    def test_home_shell_screenshot(self, page: Page, site_config):
        """WIN-VR-001：首頁 shell 截圖存檔"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        save_screenshot(screenshot_with_mask(page, BANNER_SELECTORS), "lt-home-shell.png")

    def test_login_page_screenshot(self, page: Page, site_config):
        """WIN-VR-002：登入頁表單截圖存檔"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        page.wait_for_timeout(1500)
        save_screenshot(page.screenshot(animations="disabled"), "lt-login-panel.png")

    def test_navbar_screenshot(self, page: Page, site_config):
        """WIN-VR-003：首頁上方導覽列截圖存檔"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)
        navbar = page.locator('[class*="bg-navbar"]').first
        save_screenshot(navbar.screenshot(animations="disabled"), "lt-top-nav.png")
