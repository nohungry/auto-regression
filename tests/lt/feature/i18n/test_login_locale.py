"""
LT 多語系文案驗證 — 登入頁 input placeholder（WAP 版，2026-04-22 rewrite）
WIN-I18N-LOGIN-001~005

本檔驗證：各語系切換後，登入頁 input placeholder 是否正確翻譯。

Desktop 實測 i18n 覆蓋現況（2026-05-18 換版後 probe）：
- ✅ input placeholder 有 5 語系翻譯（本檔驗證此層；selector 改為 `input.input-style` / `input.password-input`）
- ❌ `button.base-btn` 文案是否仍固定繁中尚未重新確認，本檔不驗
- ❌ `span.lang-text` 是否仍固定繁中尚未重新確認，TestI18NLangSwitcher 仍以 xfail(strict=True) 守門

與 `tests/lt/feature/copy/test_copy.py` 職責互補：
- copy：守門預設繁中文案不得變更
- 本檔：守門 placeholder i18n 翻譯對應是否完整、cookie 切換機制是否運作
"""

import pytest
from playwright.sync_api import Page, expect
from pages.lt.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter


# (case_id, locale, username_placeholder_keyword, password_placeholder_keyword)
# 只檢查關鍵字（非全字比對），避免半形/全形空格、數字中橫線變體造成 flaky。
# 2026-05-18 換版後產品動詞改了（請填寫→請輸入 / Please enter→Enter / Vui lòng điền→Vui lòng nhập），
# 改用更穩定的「該語系代表字」作 keyword，可同時 cover 新舊兩種動詞。
_PLACEHOLDER_CHECKS = [
    ("WIN-I18N-LOGIN-001", "tw", "請",        "請"),
    ("WIN-I18N-LOGIN-002", "cn", "请",        "请"),
    ("WIN-I18N-LOGIN-003", "en", "Enter",     "Enter"),
    ("WIN-I18N-LOGIN-004", "th", "กรุณา",     "กรุณา"),
    ("WIN-I18N-LOGIN-005", "vn", "Vui lòng",  "Vui lòng"),
]


@pytest.mark.p2
@pytest.mark.lt
@pytest.mark.i18n
class TestI18NLoginPage:
    """WIN-I18N-LOGIN-001~005：各語系登入頁 input placeholder 翻譯驗證"""

    @pytest.mark.parametrize("case_id,locale,username_kw,password_kw",
                             _PLACEHOLDER_CHECKS,
                             ids=[c[0] for c in _PLACEHOLDER_CHECKS])
    def test_login_placeholder_locale(self, page: Page, site_config, case_id, locale,
                                      username_kw, password_kw):
        """各語系登入頁帳號/密碼欄 placeholder 正確翻譯"""
        login = LoginPage(page, site_config.url)
        login.goto_login(locale=locale)

        sh = get_screenshotter(page)
        # 2026-05-18 換版：input.login-input → input.input-style(text) / input.password-input
        username_input = login.username_input
        password_input = login.password_input

        # 分別截圖，label 帶 placeholder 方便 review
        username_input.scroll_into_view_if_needed()
        username_placeholder = username_input.get_attribute("placeholder") or ""
        if sh: sh.capture(username_input, f"verify_{locale}_帳號placeholder_{username_placeholder[:20]}")

        password_input.scroll_into_view_if_needed()
        password_placeholder = password_input.get_attribute("placeholder") or ""
        if sh: sh.capture(password_input, f"verify_{locale}_密碼placeholder_{password_placeholder[:20]}")

        # 補一張 full_page 呈現整體登入頁語系切換效果
        if sh: sh.full_page(f"verify_{locale}_登入頁_整體")

        assert username_kw in username_placeholder, \
            f"{locale} 帳號 placeholder 未包含 '{username_kw}'：{username_placeholder}"
        assert password_kw in password_placeholder, \
            f"{locale} 密碼 placeholder 未包含 '{password_kw}'：{password_placeholder}"


@pytest.mark.p2
@pytest.mark.lt
@pytest.mark.i18n
class TestI18NLangSwitcher:
    """WIN-I18N-LANG：登入頁左上角語系切換按鈕文案應隨 locale 變化。

    產品現況（2026-04-22 probe）：`span.lang-text` 所有語系都固定顯示「繁中」，
    此測試以 xfail(strict=True) 形式登錄在案：當產品端修正 i18n 後，斷言會轉為 pass，
    strict xfail 會將 XPASS 視為失敗，提醒移除 xfail marker 並正式 enforce。
    """

    @pytest.mark.xfail(
        strict=True,
        reason="WAP 產品端尚未實作 span.lang-text i18n（所有語系固定繁中）；"
               "此 xfail 在產品修正後會 XPASS 並觸發失敗，提醒拿掉 xfail。"
    )
    def test_lang_text_reflects_locale(self, page: Page, site_config):
        """切換 5 語系後，左上角 span.lang-text 應顯示對應語系名稱（至少與 tw 不同）"""
        login = LoginPage(page, site_config.url)
        sh = get_screenshotter(page)
        lang_texts: dict[str, str] = {}

        for locale in ["tw", "cn", "en", "th", "vn"]:
            login.goto_login(locale=locale)
            lang_el = page.locator('span.lang-text').first
            expect(lang_el).to_be_visible(timeout=5000)
            lang_el.scroll_into_view_if_needed()
            text = (lang_el.inner_text() or "").strip()
            lang_texts[locale] = text
            if sh: sh.capture(lang_el, f"verify_{locale}_lang_text_{text[:10]}")

        if sh: sh.full_page(f"verify_lang_text_全語系彙整_{lang_texts}")

        # tw 必須為繁中（baseline）
        assert lang_texts["tw"] in ("繁中", "繁體中文"), \
            f"tw lang-text 預期「繁中/繁體中文」，實際：{lang_texts['tw']}"

        # 其餘語系必須與 tw 不同（代表 i18n 切換有作用）
        for loc in ["cn", "en", "th", "vn"]:
            assert lang_texts[loc] != lang_texts["tw"], \
                f"{loc} 語系 lang-text 不應仍顯示 '{lang_texts['tw']}'，實際：{lang_texts[loc]}（全部：{lang_texts}）"
