"""
多語系文案驗證
WIN-I18N-001~005
"""

import pytest
from playwright.sync_api import Page, expect
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter


_LOCALE_CHECKS = [
    ("WIN-I18N-001", "tw", ["熱門", "真人", "電子", "捕魚", "登入"],              "繁中首頁文案"),
    ("WIN-I18N-002", "cn", ["热门", "真人", "电子", "捕鱼", "登录"],              "簡中首頁文案"),
    ("WIN-I18N-003", "en", ["Hot", "Live Casino", "Slots", "Fishing", "Login"],  "英文首頁文案"),
    ("WIN-I18N-004", "th", ["ยอดฮิต", "คนจริง", "อิเล็กทรอนิกส์", "ยิงปลา", "เข้าสู่ระบบ"], "泰文首頁文案"),
    ("WIN-I18N-005", "vn", ["Phổ biến", "Người thật", "Điện tử", "Câu cá", "Đăng nhập"], "越文首頁文案"),
]


@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.i18n
class TestI18N:
    """WIN-I18N-001~005：多語系首頁文案驗證"""

    @pytest.mark.parametrize("case_id,locale,texts,title", _LOCALE_CHECKS,
                             ids=[c[0] for c in _LOCALE_CHECKS])
    def test_locale_home_text(self, page: Page, site_config, case_id, locale, texts, title):
        """各語系首頁主要文案正確顯示"""
        set_locale(page, site_config.url, locale)
        page.goto(site_config.url)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1500)

        sh = get_screenshotter(page)
        body = page.locator("body")
        for text in texts:
            expect(body).to_contain_text(text)
        if sh: sh.full_page(f"verify_{locale}_首頁文案")
