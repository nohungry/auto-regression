"""
LT 多語系文案驗證 — 登入頁欄位標籤與按鈕（職責：5 語系切換後文案對應）
WIN-I18N-LOGIN-001~005

本檔驗證各語系（tw/cn/en/th/vn）切換後，登入頁欄位/按鈕文案是否正確翻譯。
與 `tests/lt/feature/copy/test_copy.py` 職責互補：
- copy：守門預設繁中文案不得變更
- 本檔：守門 i18n 翻譯對應是否完整、切換機制是否運作

注意：「先去逛逛」按鈕在所有語系均固定顯示繁中（未翻譯，已知行為）。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.lt.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter

pytestmark = pytest.mark.skip(
    reason="LT 2026-04-19 改版：登入頁欄位結構改變，待整輪 rebuild。"
           "見 memory: project_lt_site_redesign.md"
)


_LOGIN_LOCALE_CHECKS = [
    # (case_id, locale, username_label, password_label, login_btn)
    ("WIN-I18N-LOGIN-001", "tw", "會員帳號",               "登入密碼",                 "登入"),
    ("WIN-I18N-LOGIN-002", "cn", "会员帐号",               "登录密码",                 "登录"),
    ("WIN-I18N-LOGIN-003", "en", "Username",              "Password",               "Login"),
    ("WIN-I18N-LOGIN-004", "th", "บัญชีสมาชิก",            "รหัสผ่านเข้าสู่ระบบ",      "เข้าสู่ระบบ"),
    ("WIN-I18N-LOGIN-005", "vn", "Tài khoản thành viên", "Mật khẩu đăng nhập",      "Đăng nhập"),
]


@pytest.mark.p1
@pytest.mark.lt
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
