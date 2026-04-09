"""
DRC 語系下拉選單結構驗證
驗證 globe icon 下拉選單應有 6 個語系，且每個語系名稱可見。

語系切換後的實際文案驗證，請參考：
- tests/drc/feature/i18n/test_home_locale.py      首頁 nav 文案
- tests/drc/feature/i18n/test_login_locale.py     登入表單文案
- tests/drc/feature/i18n/test_sidebar_locale.py   側邊欄文案
"""

import pytest
from playwright.sync_api import Page, expect
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present
from utils.screenshot_helper import get_screenshotter


EXPECTED_LANGUAGES = [
    "繁體中文",
    "簡体中文",
    "日本語",
    "ภาษาไทย",
    "Tiếng Việt",
    "English",
]


@pytest.mark.p1
@pytest.mark.language
class TestLanguageDropdown:
    """TC-L01：語系下拉選單結構"""

    def test_dropdown_has_six_languages(self, page: Page, site_config):
        """TC-L01：globe icon 下拉選單應有 6 個語系，且每個語系名稱可見"""
        page.goto(site_config.url)
        page.wait_for_load_state("networkidle")
        dismiss_server_error_if_present(page)
        dismiss_announcement_popup_if_present(page)
        sh = get_screenshotter(page)

        # 點擊 globe icon 開啟下拉選單
        globe = page.locator("img[src*='global']")
        globe.scroll_into_view_if_needed()
        if sh: sh.capture(globe, "click_globe_icon")
        globe.click()

        lang_items = page.locator("img[src*='global']").locator("..").locator("p.whitespace-nowrap")
        lang_items.first.wait_for(state="visible", timeout=5000)

        # 數量驗證
        expect(lang_items).to_have_count(len(EXPECTED_LANGUAGES))

        # 逐一驗證每個語系名稱可見
        for lang_name in EXPECTED_LANGUAGES:
            option = lang_items.filter(has_text=lang_name)
            expect(option).to_be_visible()
            if sh: sh.capture(option, f"verify_語系_{lang_name}")

        if sh: sh.full_page("verify_語系選單_6個語系")
