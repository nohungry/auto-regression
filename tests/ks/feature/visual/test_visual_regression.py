"""
KS 視覺截圖存檔（p2，供人工目視確認）— Super9娛樂城

鏡像 tests/qw/feature/visual/test_visual_regression.py 結構，selector 依 KS 站實作調整。
截圖存於 screenshots/ks/vr_reference/，**不做** pixel 比對
（跨環境解析度不穩定，pixel-level baseline 無法穩定運作；僅供人工目視確認）。

KS 特性：
  - 框架：Nuxt (Vue)；金色英文/简体主題（與 LG 同框架但組件細節不同）
  - 登入：modal（`.dialog-container.max-w-[388px]`，非獨立 /auth 頁）；
    `LoginPage.open_login_modal()` 從 nav「Player Login」CTA（button.gold-btn）彈出
  - 進站公告：單層（`.dialog-container.max-w-[840px]`），**fresh 載入 ~12s 才出現**
  - **dev 環境 `.dialog-mask` fade-leave-active transition 卡住**：關公告後 mask 殘留 DOM
    不移除 → home_shell / navbar 截圖前強制隱藏殘留 mask，避免畫面變暗
  - navbar 容器：`.nav-bg`
  - goto：`LoginPage.goto()` 內建 domcontentloaded + 60s timeout + 等 CTA 可見
"""

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from pages.ks.login_page import LoginPage
from pages.ks.home_page import HomePage
from tests.ks.feature.visual.helpers import BANNER_SELECTORS
from utils.visual_helpers import save_vr_screenshot, screenshot_with_mask


def _dismiss_announcement(page: Page, home: HomePage) -> None:
    """等 KS 單層進站公告 mount（fresh 載入 ~12s 才出現）後關閉。

    用較長 timeout 等公告出現再關；無公告即跳過（try/except）。
    """
    try:
        home.announce_close.wait_for(state="visible", timeout=18000)
        home.announce_close.dispatch_event("click")
    except PlaywrightTimeoutError:
        pass  # 無公告


def _clear_stuck_mask(page: Page) -> None:
    """強制隱藏殘留的 stuck `.dialog-mask`（KS dev fade-leave-active transition bug）。

    公告已關閉（close-wrap 點過），但 dev 環境 mask 不從 DOM 移除、半透明黑遮罩殘留
    會讓 reference 截圖變暗。此處純為截圖乾淨度隱藏殘留遮罩，非掩蓋產品問題
    （公告本身已正常關閉）。
    """
    page.evaluate(
        """() => {
        document.querySelectorAll('.dialog-mask').forEach(m => {
            m.style.display = 'none';
        });
    }"""
    )


@pytest.mark.p2
@pytest.mark.ks
@pytest.mark.visual_regression
class TestVisualRegression:
    """KS 截圖存檔供人工目視確認（不做 baseline 比對）"""

    def test_home_shell_screenshot(self, page: Page, site_config):
        """首頁 shell 截圖存檔（mask 動態 banner / 暫停 swiper / 關公告 + 清殘留 mask）

        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        home = HomePage(page)
        _dismiss_announcement(page, home)
        _clear_stuck_mask(page)
        page.wait_for_timeout(1000)
        save_vr_screenshot(
            screenshot_with_mask(page, BANNER_SELECTORS),
            "ks",
            "ks-home-shell.png",
        )

    def test_login_panel_screenshot(self, page: Page, site_config):
        """登入 modal 截圖存檔（KS modal 容器 .dialog-container.max-w-[388px]）

        KS 沒有獨立 /auth 頁；登入表單以 modal 形式從 nav「Player Login」CTA 叫出。
        先關進站公告，再開 modal 截圖。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        home = HomePage(page)
        _dismiss_announcement(page, home)
        login.open_login_modal()
        page.wait_for_timeout(1500)
        save_vr_screenshot(
            page.screenshot(animations="disabled"),
            "ks",
            "ks-login-panel.png",
        )

    def test_navbar_screenshot(self, page: Page, site_config):
        """首頁上方導覽列截圖存檔（KS navbar 容器：`.nav-bg`）

        先關公告 + 清殘留 mask（高 z-index 會蓋住 navbar），再截 navbar 容器。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        home = HomePage(page)
        _dismiss_announcement(page, home)
        _clear_stuck_mask(page)
        navbar = page.locator(".nav-bg").first
        navbar.wait_for(state="visible", timeout=10000)
        save_vr_screenshot(
            navbar.screenshot(animations="disabled"),
            "ks",
            "ks-top-nav.png",
        )
