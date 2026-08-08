"""
LU 視覺截圖存檔（p2，供人工目視確認）— Dlgbet

鏡像 tests/qw/feature/visual/test_visual_regression.py 結構，selector 依 LU 站實作調整。
截圖存於 screenshots/lu/vr_reference/，**不做** pixel 比對
（跨環境解析度不穩定，pixel-level baseline 無法穩定運作；僅供人工目視確認）。

LU 特性（與姊妹站 LG 差異大，勿照抄）：
  - 框架：Nuxt (Vue)；強制 tw locale（英文 title Dlgbet）
  - 登入：modal（`.dialog-container.max-w-[708px]`，非獨立 /auth 頁）；
    `LoginPage.open_login_modal()` 從 nav「登錄」CTA 彈出
  - 進站公告：**雙層**（圖片廣告 → 文字公告），**fresh 載入 ~10-12s 才出現** →
    截圖前須以 settle 迴圈等公告 mount 後依序關閉，避免 mask 殘留汙染截圖
  - navbar 容器：`.fixed.top-0.z-50`（**無 .nav-bg**）
  - goto：`LoginPage.goto()` 內建 domcontentloaded + 60s timeout + 等 CTA 可見
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_login_page_class, get_home_page_class
from tests.lu.feature.visual.helpers import BANNER_SELECTORS
from utils.visual_helpers import save_vr_screenshot, screenshot_with_mask


LoginPage = get_login_page_class("lu")
HomePage = get_home_page_class("lu")


def _settle_home(page: Page, login: LoginPage, home: HomePage) -> None:
    """等 LU 雙層進站公告 mount 後依序關閉，直到 mask 清空。

    LU 公告 fresh 載入 ~10-12s 才出現；dismiss_announcement / dismiss_any_popups
    內建 try/except，未出現即跳過。retry 迴圈確保延遲渲染的公告也被清掉
    （mask = .popup-announcement-mask 圖片廣告 + .dialog-mask 文字公告）。
    """
    for _ in range(5):
        login.dismiss_announcement()
        home.dismiss_any_popups()
        masks = page.evaluate(
            "() => document.querySelectorAll('.popup-announcement-mask, .dialog-mask').length"
        )
        if masks == 0:
            return
        page.wait_for_timeout(2000)


@pytest.mark.p2
@pytest.mark.lu
@pytest.mark.visual_regression
class TestVisualRegression:
    """LU 截圖存檔供人工目視確認（不做 baseline 比對）"""

    def test_home_shell_screenshot(self, page: Page, site_config):
        """首頁 shell 截圖存檔（mask 動態 banner / 暫停 swiper / 關雙層進站公告）

        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        home = HomePage(page)
        _settle_home(page, login, home)
        page.wait_for_timeout(1000)
        save_vr_screenshot(
            screenshot_with_mask(page, BANNER_SELECTORS),
            "lu",
            "lu-home-shell.png",
        )

    def test_login_panel_screenshot(self, page: Page, site_config):
        """登入 modal 截圖存檔（LU modal 容器 .dialog-container.max-w-[708px]）

        LU 沒有獨立 /auth 頁；登入表單以 modal 形式從首頁 nav「登錄」CTA 叫出。
        先以 settle 迴圈清掉雙層進站公告（會疊在 modal 上方），再開 modal 截圖。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        home = HomePage(page)
        _settle_home(page, login, home)
        login.open_login_modal()
        page.wait_for_timeout(1500)
        save_vr_screenshot(
            page.screenshot(animations="disabled"),
            "lu",
            "lu-login-panel.png",
        )

    def test_navbar_screenshot(self, page: Page, site_config):
        """首頁上方導覽列截圖存檔（LU navbar 容器：`.fixed.top-0.z-50`）

        先清雙層公告（mask 高 z-index 會蓋住 navbar），再截 navbar 容器。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        home = HomePage(page)
        _settle_home(page, login, home)
        navbar = page.locator(".fixed.top-0.z-50").first
        navbar.wait_for(state="visible", timeout=10000)
        save_vr_screenshot(
            navbar.screenshot(animations="disabled"),
            "lu",
            "lu-top-nav.png",
        )
