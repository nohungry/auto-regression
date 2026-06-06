"""
KS i18n 輕量驗證（Super9娛樂城）
KS-I18N-001 ~ 002

範圍（輕量：語言切換器存在性驗證）：
- 驗證語言切換 toggle（简体 / English）存在
- 驗證 Nuxt i18n_redirected cookie 已設定

probe 2026-06-06：KS 登出即顯示「简体 / English」語言 toggle，預設 i18n_redirected=cn。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.ks
@pytest.mark.i18n
class TestI18n:
    """KS-I18N-001 ~ 002：語言 toggle 存在性 + i18n cookie"""

    def test_language_toggle_present(self, page: Page, site_config):
        """KS-I18N-001：语言 toggle（English 選項）存在且可見"""
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        en_toggle = page.locator("div.cursor-pointer").filter(has_text="English").first
        expect(en_toggle).to_be_visible(timeout=15000)
        sh = get_screenshotter(page)
        if sh: sh.capture(en_toggle, "verify_語言toggle存在")

    def test_i18n_cookie_set(self, page: Page, site_config):
        """KS-I18N-002：Nuxt i18n_redirected cookie 已設定"""
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        assert cookies.get("i18n_redirected"), \
            f"預期 i18n_redirected cookie 存在，實際 cookies={list(cookies)}"
