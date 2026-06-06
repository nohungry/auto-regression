"""
LU i18n 輕量驗證（Dlgbet）
LU-I18N-001 ~ 002

範圍（輕量：語言切換器存在性驗證）：
- 驗證左側 sidebar 內語言切換項（語言）存在
- 驗證 Nuxt i18n_redirected cookie 已設定

probe 2026-06-06：LU 語言切換在登入後左側 sidebar（「語言」項），預設 i18n_redirected=tw。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lu")


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.i18n
class TestI18n:
    """LU-I18N-001 ~ 002：sidebar 語言項存在性 + i18n cookie"""

    def test_language_item_present(self, class_logged_in_page: Page, go_home):
        """LU-I18N-001：展開左側 sidebar 後「語言」切換項存在"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_user_menu()  # 展開左側 sidebar
        lang_item = page.locator(".fixed.left-0.z-30").get_by_text("語言", exact=True).first
        expect(lang_item).to_be_visible(timeout=5000)
        if sh: sh.capture(lang_item, "verify_sidebar語言項存在")

    def test_i18n_cookie_set(self, class_logged_in_page: Page, go_home, site_config):
        """LU-I18N-002：Nuxt i18n_redirected cookie 已設定"""
        page = class_logged_in_page
        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        assert cookies.get("i18n_redirected"), \
            f"預期 i18n_redirected cookie 存在，實際 cookies={list(cookies)}"
