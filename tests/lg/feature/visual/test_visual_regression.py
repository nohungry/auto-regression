"""
LG 視覺截圖存檔（p2，供人工目視確認）— 大撈家娛樂城

鏡像 tests/qw/feature/visual/test_visual_regression.py 結構，selector 依 LG 站實作調整。
截圖存於 screenshots/lg/vr_reference/，**不做** pixel 比對
（跨環境解析度不穩定，pixel-level baseline 無法穩定運作；僅供人工目視確認）。

LG 特性：
  - 框架：Nuxt (Vue)；單語系 zh-TW
  - 登入：modal（非獨立 /auth 頁）；`LoginPage.open_login_modal()` 從首頁 nav CTA 彈出
  - 進站公告：`.dialog-container.w-full`（max-w-[840px]）；`LoginPage.dismiss_announcement()`
    已 try/except 包（有就關、沒有跳過）
  - navbar 容器：`.nav-bg`
  - goto：`LoginPage.goto()` 內建 domcontentloaded + 60s timeout + 等 CTA 可見
"""

import pytest
from playwright.sync_api import Page
from pages.lg.login_page import LoginPage
from tests.lg.feature.visual.helpers import BANNER_SELECTORS
from utils.visual_helpers import save_vr_screenshot, screenshot_with_mask


@pytest.mark.p2
@pytest.mark.lg
@pytest.mark.visual_regression
class TestVisualRegression:
    """LG 截圖存檔供人工目視確認（不做 baseline 比對）"""

    def test_home_shell_screenshot(self, page: Page, site_config):
        """首頁 shell 截圖存檔（mask 動態 banner / 暫停 swiper / dismiss 進站公告）

        LG 進站公告為 `.dialog-container.w-full`；dismiss_announcement() 已 try/except 包，
        無公告即跳過。截圖前遮蔽動態 banner（BANNER_SELECTORS）並暫停 swiper。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.dismiss_announcement()
        page.wait_for_timeout(1500)
        save_vr_screenshot(
            screenshot_with_mask(page, BANNER_SELECTORS),
            "lg",
            "lg-home-shell.png",
        )

    def test_login_panel_screenshot(self, page: Page, site_config):
        """登入 modal 截圖存檔

        LG 沒有獨立 /auth 頁；登入表單以 modal 形式從首頁 nav「登入」CTA 叫出。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.dismiss_announcement()
        login.open_login_modal()
        page.wait_for_timeout(1500)
        save_vr_screenshot(
            page.screenshot(animations="disabled"),
            "lg",
            "lg-login-panel.png",
        )

    def test_navbar_screenshot(self, page: Page, site_config):
        """首頁上方導覽列截圖存檔（LG navbar 容器：`.nav-bg`）

        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1000)
        navbar = page.locator(".nav-bg").first
        navbar.wait_for(state="visible", timeout=10000)
        save_vr_screenshot(
            navbar.screenshot(animations="disabled"),
            "lg",
            "lg-top-nav.png",
        )
