"""
RD 視覺截圖存檔（p2，供人工目視確認）— 狗狗娛樂城
鏡像 tests/rc/feature/visual/test_visual_regression.py，selector 依 RD 站實作調整。

截圖存於 screenshots/rd/vr_reference/，**不做** pixel 比對。
跨環境解析度不穩定，pixel-level baseline 比對無法穩定運作；存檔僅供人工目視確認。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_login_page_class
from tests.rd.feature.visual.helpers import BANNER_SELECTORS
from utils.visual_helpers import save_vr_screenshot, screenshot_with_mask


LoginPage = get_login_page_class("rd")


@pytest.mark.p2
@pytest.mark.rd
@pytest.mark.visual_regression
class TestVisualRegression:
    """RD 截圖存檔供人工目視確認（不做 baseline 比對）"""

    def test_home_shell_screenshot(self, page: Page, site_config):
        """RD-VR-001：首頁 shell 截圖存檔（mask 動態 banner / 暫停 swiper）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        save_vr_screenshot(
            screenshot_with_mask(page, BANNER_SELECTORS),
            "rd",
            "rd-home-shell.png",
        )

    def test_login_panel_screenshot(self, page: Page, site_config):
        """RD-VR-002：登入表單截圖存檔

        RD 沒有獨立 /login 頁；登入表單以 modal 形式從首頁右上「登錄」叫出。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        page.wait_for_timeout(1500)
        save_vr_screenshot(
            page.screenshot(animations="disabled"),
            "rd",
            "rd-login-panel.png",
        )

    def test_navbar_screenshot(self, page: Page, site_config):
        """RD-VR-003：首頁上方導覽列截圖存檔

        RD navbar 容器無 `nav` / `.nav-bg`，用 `bg-shade04 border-b` 組合鎖定
        （flex 容器，h-[54px]/lg:h-[86px]，含 logo + lang button + 登錄 + Chat）。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)
        navbar = page.locator("div.bg-shade04.border-b").first
        save_vr_screenshot(
            navbar.screenshot(animations="disabled"),
            "rd",
            "rd-top-nav.png",
        )
