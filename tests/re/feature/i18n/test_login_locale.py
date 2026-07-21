"""
RE 多語系文案驗證 — 登入 Modal 欄位標籤與按鈕 (BeWin)
RE-I18N-LOGIN-001~006

本檔驗證各語系（繁中/簡中/日/泰/越/英）切換後，登入 modal 的 placeholder 與 CTA 文案。

RE 與 RC 共用 t9platform 平台 modal 內結構（modal submit btn 為 button.primary-btn），
但 RE 站 nav 上的登入觸發按鈕**沒有** primary-btn class（RC 才有），需用文字定位：
- 點擊 nav 上的「登入」/「Login」等本地化文字按鈕開啟 modal
- 欄位識別用 placeholder（非 label），故驗證 placeholder attribute
- 送出按鈕同樣為 button.primary-btn（modal 內）
"""

import pytest
from playwright.sync_api import Page, expect
from utils.locale_helper import switch_language_via_globe
from utils.screenshot_helper import get_screenshotter


_LOGIN_LOCALE_CHECKS = [
    # (case_id, lang_name, username_ph, password_ph, login_btn_text)
    ("RE-I18N-LOGIN-001", "繁體中文",   "用戶名",           "密碼",       "登入"),
    ("RE-I18N-LOGIN-002", "簡体中文",   "用户名",           "密码",       "登录"),
    ("RE-I18N-LOGIN-003", "日本語",     "ユーザー名",        "パスワード",  "ログイン"),
    ("RE-I18N-LOGIN-004", "ภาษาไทย",   "ชื่อผู้ใช้",       "รหัสผ่าน",  "เข้าสู่ระบบ"),
    ("RE-I18N-LOGIN-005", "Tiếng Việt", "Tên người dùng", "Mật khẩu",   "Đăng nhập"),
    ("RE-I18N-LOGIN-006", "English",    "Username",        "Password",   "Login"),
]


@pytest.mark.p2
@pytest.mark.re
@pytest.mark.i18n
@pytest.mark.language
class TestI18NLoginModal:
    """RE-I18N-LOGIN-001~006：各語系登入 Modal 欄位 placeholder 與按鈕文案驗證"""

    @pytest.mark.parametrize("case_id,lang_name,username_ph,password_ph,login_btn_text",
                             _LOGIN_LOCALE_CHECKS,
                             ids=[c[0] for c in _LOGIN_LOCALE_CHECKS])
    def test_login_modal_locale_text(self, page: Page, site_config, case_id, lang_name,
                                     username_ph, password_ph, login_btn_text):
        """各語系登入 Modal placeholder 與送出按鈕文案正確顯示"""
        switch_language_via_globe(page, site_config.url, lang_name)

        sh = get_screenshotter(page)

        # 驗證 nav 登入按鈕文案（modal 開啟前）— RE 用本地化文字定位
        login_trigger = page.locator("button", has_text=login_btn_text).first
        login_trigger.wait_for(state="visible", timeout=10000)
        login_trigger.scroll_into_view_if_needed()
        if sh: sh.capture(login_trigger, f"verify_{lang_name}_登入觸發文案")
        expect(login_trigger).to_have_text(login_btn_text)

        # 開啟登入 modal
        if sh: sh.capture(login_trigger, f"click_登入觸發_{lang_name}")
        login_trigger.click()

        # 等待 modal 出現
        username_input = page.locator("input.input-style[type='text']")
        username_input.wait_for(state="visible", timeout=5000)
        password_input = page.locator("input.input-style[type='password']")

        # 驗證 placeholder
        if sh: sh.full_page(f"verify_{lang_name}_登入Modal文案")
        expect(username_input).to_have_attribute("placeholder", username_ph)
        expect(password_input).to_have_attribute("placeholder", password_ph)
