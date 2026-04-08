"""
多語系文案驗證 — 首頁 nav
DRC-I18N-HOME-001~006

語系切換方式：點擊 globe icon（img[src*='global']）→ 選擇語系名稱
"""

import pytest
from playwright.sync_api import Page, expect
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present
from utils.screenshot_helper import get_screenshotter


_HOME_LOCALE_CHECKS = [
    # (case_id, lang_name, nav_texts, title)
    ("DRC-I18N-HOME-001", "繁體中文", ["首頁", "真人", "電子", "捕魚", "登入"],                                          "繁中首頁文案"),
    ("DRC-I18N-HOME-002", "簡体中文", ["首页", "真人", "电子", "捕鱼", "登录"],                                          "簡中首頁文案"),
    ("DRC-I18N-HOME-003", "日本語",   ["トップ", "ライブ", "電子", "フィッシング", "ログイン"],                             "日文首頁文案"),
    ("DRC-I18N-HOME-004", "ภาษาไทย", ["หน้าแรก", "ถ่ายทอดสด", "อิเล็กทรอนิกส์", "เกมยิงปลา", "เข้าสู่ระบบ"],        "泰文首頁文案"),
    ("DRC-I18N-HOME-005", "Tiếng Việt", ["Trang đầu", "Người thật", "Điện tử", "Câu cá", "Đăng nhập"],               "越文首頁文案"),
    ("DRC-I18N-HOME-006", "English",  ["Home", "Live Casino", "Slots", "Fishing", "Login"],                           "英文首頁文案"),
]


def _switch_language(page: Page, url: str, lang_name: str):
    """前往首頁 → dismiss 彈窗 → globe icon 切換語系"""
    page.goto(url, wait_until="networkidle")
    dismiss_server_error_if_present(page)
    dismiss_announcement_popup_if_present(page, timeout=3000)
    globe = page.locator("img[src*='global']")
    globe.scroll_into_view_if_needed()
    globe.click()
    lang_option = page.locator("p.whitespace-nowrap", has_text=lang_name).first
    lang_option.wait_for(state="visible", timeout=5000)
    lang_option.click()
    page.wait_for_load_state("networkidle")
    dismiss_server_error_if_present(page)


@pytest.mark.p1
@pytest.mark.i18n
@pytest.mark.language
class TestI18NHome:
    """DRC-I18N-HOME-001~006：多語系首頁 nav 文案驗證"""

    @pytest.mark.parametrize("case_id,lang_name,texts,title", _HOME_LOCALE_CHECKS,
                             ids=[c[0] for c in _HOME_LOCALE_CHECKS])
    def test_locale_home_text(self, page: Page, site_config, case_id, lang_name, texts, title):
        """各語系首頁 nav 主要文案正確顯示"""
        _switch_language(page, site_config.url, lang_name)

        sh = get_screenshotter(page)
        body = page.locator("body")
        for text in texts:
            expect(body).to_contain_text(text)
        if sh: sh.full_page(f"verify_{lang_name}_首頁文案")
