"""
LG i18n 輕量驗證（大撈家娛樂城）
LG-I18N-001 ~ 002

範圍（使用者選定「輕量：語言切換器存在性驗證」）：
- 驗證 nav 語言切換器存在（不做全文案對照矩陣）
- 驗證 Nuxt i18n_redirected cookie 已設定（確認 i18n 模組啟用）

probe 2026-06-06：LG nav 有「語言」切換器（div.bg-[#c86b2e]），預設 i18n_redirected=tw。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.lg
@pytest.mark.i18n
class TestI18n:
    """LG-I18N-001 ~ 002：語言切換器存在性 + i18n cookie"""

    def test_language_switcher_present(self, page: Page, site_config):
        """LG-I18N-001：nav 語言切換器 scaffold 存在於 DOM

        注意：LG「語言」元素為零尺寸/hover 式 tooltip（probe 2026-06-06：w=0 h=0，
        非常駐可見控制項），故以 DOM 存在（count）驗證 scaffold，而非 to_be_visible。
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        switcher = page.locator("div.bg-\\[\\#c86b2e\\]").filter(has_text="語言")
        expect(switcher).to_have_count(1, timeout=15000)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_語言切換器scaffold存在")

    def test_i18n_cookie_set(self, page: Page, site_config):
        """LG-I18N-002：Nuxt i18n_redirected cookie 已設定（i18n 模組啟用）"""
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        assert cookies.get("i18n_redirected"), \
            f"預期 i18n_redirected cookie 存在，實際 cookies={list(cookies)}"
