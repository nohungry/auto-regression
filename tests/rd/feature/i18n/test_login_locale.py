"""
RD 多語系文案驗證 — 登入 Modal 欄位 placeholder 與按鈕文字 (狗狗娛樂城)
RD-I18N-LOGIN-001 ~ 005

驗證切換各語系（繁中/簡中/英/越/日）後，登入 modal 的 username/password placeholder
與 navbar 觸發按鈕、submit 按鈕文案。

RD 站 navbar 沒有 globe icon，語言觸發是 `button` 顯示當前語言名稱，
切換 dropdown 是 `div.cursor-pointer p` 顯示語系名。

NOTE: dev-rd 簡体中文版 username placeholder 為「帳號」（與其他繁體欄位混用），
看似翻譯遺漏。本測試以 dev 站當前文案為準（**as-is**），
若產品端修為「账号」則此測試會 fail，視為 i18n regression 訊號。
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_dialog_mask_if_present
from utils.screenshot_helper import get_screenshotter


# (case_id, lang_name, ph_user, ph_pwd, login_text)
_LOGIN_LOCALE_CHECKS = [
    ("RD-I18N-LOGIN-001", "繁體中文",   "帳號",         "密碼",     "登錄"),
    ("RD-I18N-LOGIN-002", "簡体中文",   "帳號",         "密码",     "登录"),
    ("RD-I18N-LOGIN-003", "日本語",     "アカウント",    "パスワード", "ログイン"),
    ("RD-I18N-LOGIN-004", "Tiếng Việt", "Tài khoản",   "Mật khẩu", "Đăng nhập"),
    ("RD-I18N-LOGIN-005", "English",    "User Name",    "Password", "Login"),
]


def _switch_language(page: Page, base_url: str, lang_name: str):
    """前往首頁 → 關掉公告蓋板 → 點當前語言觸發按鈕 → 從 dropdown 選擇目標語言

    觸發按鈕 text 隨當前語系變化，故用 `button.bg-shade03` + 多語名 alternation 定位。
    需先 dismiss_dialog_mask_if_present 關公告蓋板，否則 navbar click 會被攔截。
    """
    import re as _re
    page.goto(base_url, wait_until="domcontentloaded")
    dismiss_server_error_if_present(page)
    dismiss_dialog_mask_if_present(page)

    # 觸發按鈕（顯示當前語言）— 用 class 鎖定，filter 用任一已知語名（current state 不可預測）
    # NOTE: 此按鈕的 click handler 無法被 Playwright `.click()` 觸發（實測 dropdown 不展開），
    # 必須用 `dispatch_event("click")` 才會 toggle dropdown 狀態。
    # SPA hydration race：click handler 在 ~3-4s 後才綁上，dispatch 前需等 hydration 完成。
    lang_trigger = page.locator("button.bg-shade03").filter(
        has_text=_re.compile("繁體中文|簡体中文|日本語|Tiếng Việt|English")
    ).first
    expect(lang_trigger).to_be_visible(timeout=10000)
    lang_trigger.scroll_into_view_if_needed()

    target = page.locator("div.cursor-pointer p", has_text=lang_name).first
    # Retry pattern：第一次 dispatch 可能 hydration 未完成；3s 內 dropdown 沒展開則重試一次
    lang_trigger.dispatch_event("click")
    try:
        target.wait_for(state="visible", timeout=3000)
    except PlaywrightTimeoutError:
        page.wait_for_timeout(2000)
        lang_trigger.dispatch_event("click")
        target.wait_for(state="visible", timeout=10000)
    target.dispatch_event("click")

    # 切換後等 SPA re-hydrate
    page.wait_for_timeout(800)


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.i18n
@pytest.mark.language
class TestI18NLoginModal:
    """RD-I18N-LOGIN-001 ~ 005：登入 Modal placeholder 與 submit 文案"""

    @pytest.mark.parametrize(
        "case_id,lang_name,ph_user,ph_pwd,login_text",
        _LOGIN_LOCALE_CHECKS,
        ids=[c[0] for c in _LOGIN_LOCALE_CHECKS],
    )
    def test_login_modal_locale_text(self, page: Page, site_config, case_id, lang_name,
                                     ph_user, ph_pwd, login_text):
        """各語系登入 Modal placeholder 與 submit 按鈕文案正確顯示"""
        _switch_language(page, site_config.url, lang_name)

        sh = get_screenshotter(page)

        # 驗證 navbar 登入觸發按鈕文案（modal 開啟前）
        nav_login = page.locator("button.neon-btn", has_text=login_text).first
        expect(nav_login).to_be_visible(timeout=10000)
        if sh: sh.capture(nav_login, f"verify_{lang_name}_navbar_登入文案")
        expect(nav_login).to_have_text(login_text)

        # 開啟登入 modal — dialog-mask 已關，可用普通 click；
        # 但保險：login_page.open_login_form 用 dispatch_event 是因為 hydration race，
        # 此處遵循該 pattern
        if sh: sh.capture(nav_login, f"click_{lang_name}_開啟登入modal")
        nav_login.dispatch_event("click")

        username_input = page.locator("input").nth(0)
        username_input.wait_for(state="visible", timeout=5000)
        password_input = page.locator("input").nth(1)
        submit_btn = page.locator("button.main-btn").filter(has_text=login_text).first

        if sh: sh.full_page(f"verify_{lang_name}_登入Modal文案")
        expect(username_input).to_have_attribute("placeholder", ph_user)
        expect(password_input).to_have_attribute("placeholder", ph_pwd)
        expect(submit_btn).to_have_text(login_text)
