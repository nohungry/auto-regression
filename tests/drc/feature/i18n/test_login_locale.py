"""
多語系文案驗證 — 登入 Modal 欄位標籤與按鈕
DRC-I18N-LOGIN-001~006

DRC 登入為 Modal 形式（非獨立頁面）：
- 點擊 button.primary-btn（首頁 nav 的登入按鈕）開啟 modal
- 欄位識別用 placeholder（非 label），故驗證 placeholder attribute
- 送出按鈕同樣為 button.primary-btn（modal 內）
"""

import pytest
from playwright.sync_api import Page, expect
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present
from utils.screenshot_helper import get_screenshotter


_LOGIN_LOCALE_CHECKS = [
    # (case_id, lang_name, username_ph, password_ph, login_btn_text)
    ("DRC-I18N-LOGIN-001", "繁體中文",   "用戶名",           "密碼",       "登入"),
    ("DRC-I18N-LOGIN-002", "簡体中文",   "用户名",           "密码",       "登录"),
    ("DRC-I18N-LOGIN-003", "日本語",     "ユーザー名",        "パスワード",  "ログイン"),
    ("DRC-I18N-LOGIN-004", "ภาษาไทย",   "ชื่อผู้ใช้",       "รหัสผ่าน",  "เข้าสู่ระบบ"),
    ("DRC-I18N-LOGIN-005", "Tiếng Việt", "Tên người dùng", "Mật khẩu",   "Đăng nhập"),
    ("DRC-I18N-LOGIN-006", "English",    "Username",        "Password",   "Login"),
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
class TestI18NLoginModal:
    """DRC-I18N-LOGIN-001~006：各語系登入 Modal 欄位 placeholder 與按鈕文案驗證"""

    @pytest.mark.parametrize("case_id,lang_name,username_ph,password_ph,login_btn_text",
                             _LOGIN_LOCALE_CHECKS,
                             ids=[c[0] for c in _LOGIN_LOCALE_CHECKS])
    def test_login_modal_locale_text(self, page: Page, site_config, case_id, lang_name,
                                     username_ph, password_ph, login_btn_text):
        """各語系登入 Modal placeholder 與送出按鈕文案正確顯示"""
        _switch_language(page, site_config.url, lang_name)

        sh = get_screenshotter(page)

        # 驗證 nav 登入按鈕文案（modal 開啟前）
        login_trigger = page.locator("button.primary-btn")
        expect(login_trigger).to_have_text(login_btn_text)

        # 開啟登入 modal
        login_trigger.scroll_into_view_if_needed()
        if sh: sh.capture(login_trigger, f"click_登入觸發_{lang_name}")
        login_trigger.click()

        # 等待 modal 出現
        username_input = page.locator("input.input-style[type='text']")
        username_input.wait_for(state="visible", timeout=5000)
        password_input = page.locator("input.input-style[type='password']")

        # 驗證 placeholder
        expect(username_input).to_have_attribute("placeholder", username_ph)
        expect(password_input).to_have_attribute("placeholder", password_ph)
        if sh: sh.full_page(f"verify_{lang_name}_登入Modal文案")
