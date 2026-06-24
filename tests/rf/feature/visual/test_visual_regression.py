"""
RF 視覺截圖存檔（p2，供人工目視確認）— 金爺娛樂城

截圖存於 screenshots/rf/vr_reference/，**不做** pixel 比對
（跨環境解析度不穩定，pixel-level baseline 無法穩定運作；僅供人工目視確認）。

RF 特性：
  - 框架：Nuxt (Vue)；信用版；多語系（tw/cn/en/vi/th）
  - 登入：獨立 /Login 路由（非 modal）；a.btn-login 點後導頁至 /Login
  - 進站公告：base-modal（.base-modal__container）形式；
    LoginPage.goto() 已防禦性清除（_dismiss_base_modals）
  - 首頁 navbar 容器：nav.menu_nav（主導覽）、.loginInBox（帳號/信用區）
  - 主輪播 banner：.slider-arrow / .slider-dot（控制項）
  - 跑馬燈：.marqueeBoxs
  - goto：LoginPage.goto() 內建 domcontentloaded + 60s timeout + 等 a.btn-login 可見

截圖清單：
  1. rf-home-shell.png      — 未登入首頁 shell（mask 動態元素 / 暫停 swiper）
  2. rf-login-page.png      — /Login 頁登入表單
  3. rf-navbar-menu.png     — 首頁主導覽列（nav.menu_nav）
"""

import pytest
from playwright.sync_api import Page
from pages.rf.login_page import LoginPage
from tests.rf.feature.visual.helpers import BANNER_SELECTORS
from utils.visual_helpers import save_vr_screenshot, screenshot_with_mask


@pytest.mark.p2
@pytest.mark.rf
@pytest.mark.visual_regression
class TestVisualRegression:
    """RF 截圖存檔供人工目視確認（不做 baseline 比對）"""

    def test_home_shell_screenshot(self, page: Page, site_config):
        """首頁 shell 截圖存檔（未登入，mask 動態 banner / 跑馬燈 / 輪播控制 / 暫停 swiper）

        RF goto() 已防禦性清除 base-modal（進站公告）。
        BANNER_SELECTORS 涵蓋：.slider-arrow / .slider-dot（輪播控制）、
        .marqueeBoxs（跑馬燈）、.gameShowcaseSection（遊戲展示輪播）、banner img。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)
        save_vr_screenshot(
            screenshot_with_mask(page, BANNER_SELECTORS),
            "rf",
            "rf-home-shell.png",
        )

    def test_login_page_screenshot(self, page: Page, site_config):
        """登入頁（/Login）截圖存檔

        RF 採獨立 /Login 路由（非 modal），點首頁 a.btn-login 導頁至 /Login。
        LoginPage.open_login_form() 負責點擊並等 #desktop-account 可見。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        page.wait_for_timeout(1000)
        save_vr_screenshot(
            page.screenshot(animations="disabled"),
            "rf",
            "rf-login-page.png",
        )

    def test_navbar_menu_screenshot(self, page: Page, site_config):
        """首頁主導覽列截圖存檔（nav.menu_nav 容器）

        nav.menu_nav 包含首頁/真人/電子/捕魚等分類 button 及語言選擇器。
        進站公告 goto() 已防禦性清除，不需額外 dismiss。
        斷言策略：截圖存檔供人工 review，不做 pixel 比對。
        不吞 timeout：nav.menu_nav 為首頁常駐主導覽，若找不到（如 selector 過時/被重命名）
        應讓測試 FAIL 以提醒維護者，不可靜默 fallback 而 pass（避免掩蓋 selector regression）。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1000)
        navbar = page.locator("nav.menu_nav").first
        navbar.wait_for(state="visible", timeout=10000)
        save_vr_screenshot(
            navbar.screenshot(animations="disabled"),
            "rf",
            "rf-navbar-menu.png",
        )
