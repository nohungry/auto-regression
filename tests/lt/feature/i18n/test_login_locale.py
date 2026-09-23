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
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lt")


# (case_id, locale, username_placeholder_keyword, password_placeholder_keyword)
# 只檢查關鍵字（非全字比對），避免半形/全形空格、標點變體造成 flaky。
# 2026-09-13 第三次換版（RC 模板化）後 placeholder 由「動詞句」改為「名詞」
# （請填寫8-20位的字母或數字 → 用戶名 / 密碼），舊的動詞 keyword（請/请/Enter/
# กรุณา/Vui lòng）全部失效。實機 probe 確認 5 語系皆有翻譯，故改用各語系名詞。
_PLACEHOLDER_CHECKS = [
    ("WIN-I18N-LOGIN-001", "tw", "用戶名",          "密碼"),
    ("WIN-I18N-LOGIN-002", "cn", "用户名",          "密码"),
    ("WIN-I18N-LOGIN-003", "en", "Username",       "Password"),
    ("WIN-I18N-LOGIN-004", "th", "ชื่อผู้ใช้",          "รหัสผ่าน"),
    ("WIN-I18N-LOGIN-005", "vn", "Tên người dùng", "Mật khẩu"),
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
        # 2026-09-13 換版：改用 POM 的 input.input-style[type=text|password]
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

    產品現況（2026-09-13 probe 更新）：第三次換版後**登入頁已完全沒有語系切換入口**
    （`span.lang-text` count=0，語系切換只剩首頁 navbar `img[alt="global"]`），
    斷言必然失敗故維持 xfail(strict=True)。語意已從「i18n 未實作」變成「入口被移除」，
    是否要改為驗首頁 globe 切換待產品/測試設計確認（見本次 LT 換版報告 (b) 類）。
    """

    @pytest.mark.xfail(
        strict=True,
        reason="登入頁語系切換入口已於 2026-07-23 換版移除（probe 2026-09-13：span.lang-text count=0），"
               "斷言恆失敗故維持 xfail(strict)。待決定改驗首頁 navbar globe 切換後再重寫本測試。"
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
