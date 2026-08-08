"""
RE 視覺截圖存檔（p2，供人工目視確認）— BeWin
鏡像 tests/rc/feature/visual/test_visual_regression.py，selector 共用平台。

截圖存於 screenshots/re/vr_reference/，不做 pixel 比對。
因各人螢幕解析度不同，pixel-level baseline 比對無法跨環境穩定運作。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_login_page_class
from tests.re.feature.visual.helpers import BANNER_SELECTORS
from utils.visual_helpers import save_vr_screenshot, screenshot_with_mask


LoginPage = get_login_page_class("re")


@pytest.mark.p2
@pytest.mark.re
@pytest.mark.visual_regression
class TestVisualRegression:
    """RE 截圖存檔供人工目視確認（不做 baseline 比對）"""

    def test_home_shell_screenshot(self, page: Page, site_config):
        """首頁 shell 截圖存檔（mask 動態 banner / 暫停 swiper）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        save_vr_screenshot(screenshot_with_mask(page, BANNER_SELECTORS), "re", "re-home-shell.png")

    def test_login_panel_screenshot(self, page: Page, site_config):
        """登入表單截圖存檔
        RE 沒有獨立 /login 頁；登入表單以 modal 形式從首頁右上「登入」叫出。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        page.wait_for_timeout(1500)
        save_vr_screenshot(page.screenshot(animations="disabled"), "re", "re-login-panel.png")

    def test_navbar_screenshot(self, page: Page, site_config):
        """首頁上方導覽列截圖存檔（.nav-bg 容器）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)
        navbar = page.locator('.nav-bg').first
        save_vr_screenshot(navbar.screenshot(animations="disabled"), "re", "re-top-nav.png")
