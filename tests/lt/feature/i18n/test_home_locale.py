"""
多語系文案驗證 — 首頁 nav（WAP 版，2026-04-22 rewrite）
WIN-I18N-001~005

WAP 現況（2026-04-22 probe，5 語系皆驗證）：
- `.cat-btn`（遊戲大廳/我的最愛/台灣真人/國際真人/更多）所有語系都固定繁中顯示。
- 底部 tabbar（排行榜/公告/維護/個人）所有語系都固定繁中顯示。
- 首頁 nav 層尚未套 i18n 機制，`i18n_redirected_lt` cookie 只作用在登入頁 placeholder。

因此本檔在產品端補完首頁 nav i18n 前全部 skip（語系文案斷言無法通過且無意義）。
改測 `test_login_locale.py`（placeholder i18n 現況可驗）。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter

pytestmark = pytest.mark.skip(
    reason="產品缺口：desktop 版首頁 swipe sections（來財獨家/爆分精選/活動專區）與部分 nav 尚未套 i18n，"
           "所有語系固定繁中（probe 2026-06-27；footer 維護/公告/排行榜 tab 其實有翻譯，但 section 標題等未翻）。"
           "待產品端補首頁多語系後 un-skip。見 docs/product-bugs-to-report.md（LT i18n）。"
)


_LOCALE_CHECKS = [
    ("WIN-I18N-001", "tw", ["熱門", "真人", "電子", "捕魚", "登入"],              "繁中首頁文案"),
    ("WIN-I18N-002", "cn", ["热门", "真人", "电子", "捕鱼", "登录"],              "簡中首頁文案"),
    ("WIN-I18N-003", "en", ["Hot", "Live Casino", "Slots", "Fishing", "Login"],  "英文首頁文案"),
    ("WIN-I18N-004", "th", ["ยอดฮิต", "คนจริง", "อิเล็กทรอนิกส์", "ยิงปลา", "เข้าสู่ระบบ"], "泰文首頁文案"),
    ("WIN-I18N-005", "vn", ["Phổ biến", "Người thật", "Điện tử", "Câu cá", "Đăng nhập"], "越文首頁文案"),
]


@pytest.mark.p2
@pytest.mark.lt
@pytest.mark.i18n
class TestI18NHome:
    """WIN-I18N-001~005：多語系首頁 nav 文案驗證"""

    @pytest.mark.parametrize("case_id,locale,texts,title", _LOCALE_CHECKS,
                             ids=[c[0] for c in _LOCALE_CHECKS])
    def test_locale_home_text(self, page: Page, site_config, case_id, locale, texts, title):
        """各語系首頁主要文案正確顯示"""
        set_locale(page, site_config.url, locale)
        page.goto(site_config.url)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1500)

        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_{locale}_首頁文案")
        body = page.locator("body")
        for text in texts:
            expect(body).to_contain_text(text)
