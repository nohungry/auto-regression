"""
多語系文案驗證 — 登入頁欄位標籤與按鈕
WIN-I18N-LOGIN-001~005

注意：「先去逛逛」按鈕在所有語系均固定顯示繁中（未翻譯，已知行為）
"""

import pytest
from playwright.sync_api import Page, expect
from pages.dlt.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter


_LOGIN_LOCALE_CHECKS = [
    # (case_id, locale, username_label, password_label, login_btn)
    ("WIN-I18N-LOGIN-001", "tw", "會員帳號",               "登入密碼",                 "登入"),
    ("WIN-I18N-LOGIN-002", "cn", "会员帐号",               "登录密码",                 "登录"),
    ("WIN-I18N-LOGIN-003", "en", "Username",              "Password",               "Login"),
    ("WIN-I18N-LOGIN-004", "th", "บัญชีสมาชิก",            "รหัสผ่านเข้าสู่ระบบ",      "เข้าสู่ระบบ"),
    ("WIN-I18N-LOGIN-005", "vn", "Tài khoản thành viên", "Mật khẩu đăng nhập",      "Đăng nhập"),
]


@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.i18n
class TestI18NLoginPage:
    """WIN-I18N-LOGIN-001~005：各語系登入頁欄位標籤與按鈕文案驗證"""

    @pytest.mark.parametrize("case_id,locale,username_label,password_label,login_btn",
                             _LOGIN_LOCALE_CHECKS,
                             ids=[c[0] for c in _LOGIN_LOCALE_CHECKS])
    def test_login_page_locale_text(self, page: Page, site_config, case_id, locale,
                                    username_label, password_label, login_btn):
        """各語系登入頁欄位標籤、按鈕文案正確顯示
        「先去逛逛」在所有語系固定顯示繁中（未翻譯，屬已知行為）。
        """
        login = LoginPage(page, site_config.url)
        login.goto_login(locale=locale)

        sh = get_screenshotter(page)
        body = page.locator("body")
        expect(body).to_contain_text(username_label)
        expect(body).to_contain_text(password_label)
        expect(page.locator("button").first).to_have_text(login_btn)
        expect(body).to_contain_text("先去逛逛")
        if sh: sh.full_page(f"verify_{locale}_登入頁文案")
