"""
視覺截圖存檔（p2，供人工目視確認）— QW 站（LM來財娛樂城）
對齊 tests/rc/feature/visual/test_visual_regression.py 結構，selector 換成 QW 自己的。

截圖存於 screenshots/qw/vr_reference/，不做 pixel 比對。
因各人螢幕解析度不同，pixel-level baseline 比對無法跨環境穩定運作。

QW 特性：
  - 框架：Nuxt (Vue)；多語系（LaiBetLanguage cookie）
  - 公告彈窗：.popup-mask + .popup-close（首頁未登入也會顯示）
  - 登入頁：獨立 /auth 頁（LoginPage.goto() 直接導向 /auth）
  - 首頁 goto：wait_until="domcontentloaded"（背景 polling 不會到 networkidle）
  - Navbar selector：待 probe 確認，fallback 策略：依序試 header / nav / .nav-bg
"""

import pytest
from playwright.sync_api import Page
from pages.qw.login_page import LoginPage
from pages.qw.home_page import HomePage
from tests.qw.feature.visual.helpers import BANNER_SELECTORS
from utils.visual_helpers import save_vr_screenshot, screenshot_with_mask


@pytest.mark.p2
@pytest.mark.qw
@pytest.mark.visual_regression
class TestVisualRegression:
    """QW 截圖存檔供人工目視確認（不做 baseline 比對）"""

    def test_home_shell_screenshot(self, page: Page, site_config):
        """首頁 shell 截圖存檔（mask 動態 banner / 暫停 swiper / dismiss 公告 popup）

        QW 首頁有公告 popup-mask 會擋畫面，截圖前必須先 dismiss_any_popups()。
        使用 domcontentloaded（QW 首頁背景 polling 不會 networkidle，已於 P0 smoke verify）。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        page.goto(site_config.url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        home = HomePage(page)
        home.dismiss_any_popups()

        save_vr_screenshot(screenshot_with_mask(page, BANNER_SELECTORS), "qw", "qw-home-shell.png")

    def test_auth_page_screenshot(self, page: Page, site_config):
        """登入頁截圖存檔（QW 的 /auth 是獨立頁，非 modal）

        LoginPage.goto() 已使用 networkidle 保護 Nuxt hydration，
        此 case 直接呼叫即可。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)
        save_vr_screenshot(page.screenshot(animations="disabled"), "qw", "qw-auth-page.png")

    def test_navbar_screenshot(self, page: Page, site_config):
        """頂部導覽列截圖存檔

        QW navbar 容器：`.nav-row`（probe 確認，1920×74，含 logo + nav items + 登入按鈕）。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        page.goto(site_config.url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        navbar = page.locator('.nav-row').first
        save_vr_screenshot(navbar.screenshot(animations="disabled"), "qw", "qw-top-nav.png")
