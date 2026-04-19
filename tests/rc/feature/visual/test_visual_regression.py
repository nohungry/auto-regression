"""
視覺截圖存檔（p2，供人工目視確認）— RC 站
鏡像 tests/lt/feature/visual/test_visual_regression.py，selector 依 RC 站實作調整。

截圖存於 screenshots/rc/vr_reference/，不做 pixel 比對。
因各人螢幕解析度不同，pixel-level baseline 比對無法跨環境穩定運作。
"""

import pytest
from playwright.sync_api import Page
from pages.rc.login_page import LoginPage
from tests.rc.feature.visual.helpers import BANNER_SELECTORS
from utils.visual_helpers import save_vr_screenshot, screenshot_with_mask


@pytest.mark.p2
@pytest.mark.rc
@pytest.mark.visual_regression
class TestVisualRegression:
    """RC 截圖存檔供人工目視確認（不做 baseline 比對）"""

    def test_home_shell_screenshot(self, page: Page, site_config):
        """首頁 shell 截圖存檔（mask 動態 banner / 暫停 swiper）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        save_vr_screenshot(screenshot_with_mask(page, BANNER_SELECTORS), "rc", "rc-home-shell.png")

    def test_login_panel_screenshot(self, page: Page, site_config):
        """登入表單截圖存檔
        RC 沒有獨立 /login 頁；登入表單以 modal/側欄形式從首頁右上「登入」叫出。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        page.wait_for_timeout(1500)
        save_vr_screenshot(page.screenshot(animations="disabled"), "rc", "rc-login-panel.png")

    def test_navbar_screenshot(self, page: Page, site_config):
        """首頁上方導覽列截圖存檔（.nav-bg 容器）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)
        navbar = page.locator('.nav-bg').first
        save_vr_screenshot(navbar.screenshot(animations="disabled"), "rc", "rc-top-nav.png")
