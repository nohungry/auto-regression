"""
RE P0 Smoke Test (BeWin)
每次 Release 必跑，只保留核心健康度流程（登入、首頁載入、登出、登入表單可見性）。

功能型測試已遷移：
- 個人資訊 / 站內信  → tests/re/feature/member/test_member.py
- 首頁區塊（熱門/最新/公告/餘額）→ tests/re/feature/home_sections/test_home_sections.py
- 側邊欄彈窗（遊戲明細 / BeWin 公告 / 未登入跳登入）→ tests/re/feature/sidebar/test_sidebar.py
- 真人廳館顯示             → tests/re/feature/navigation/test_navigation.py
- 分類頁跳轉（真人/電子/捕魚）→ tests/re/feature/navigation/test_navigation.py
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class, get_home_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("re")
HomePage = get_home_page_class("re")


@pytest.mark.p0
@pytest.mark.re
@pytest.mark.login
class TestLogin:
    """RE-TC-001 ~ RE-TC-004：登入相關"""

    def test_login_success(self, page: Page, site_config):
        """RE-TC-001：正常登入"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_wrong_password(self, page: Page, site_config):
        """RE-TC-002：正確帳號 + 錯誤密碼應失敗，並出現「密碼錯誤」警告彈窗

        RE 警告彈窗結構（與 RC toast 不同）：
        - 標題：「警告」
        - 訊息：「密碼錯誤」
        - 按鈕：純文字「確定」（class 非 toast-confirm-btn）
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login(site_config.username, "wrong_password_123")

        warning_title = page.locator("text=警告").first
        error_msg = page.locator("text=密碼錯誤").first
        confirm_btn = page.locator("button:not(.toast-confirm-btn)", has_text="確定").first
        sh = get_screenshotter(page)
        if sh: sh.capture(warning_title, "verify_警告標題")
        if sh: sh.capture(error_msg, "verify_密碼錯誤訊息")
        if sh: sh.capture(confirm_btn, "verify_確定按鈕")
        expect(warning_title).to_be_visible(timeout=5000)
        expect(error_msg).to_be_visible()
        expect(confirm_btn).to_be_visible()

    def test_login_wrong_username(self, page: Page, site_config):
        """RE-TC-003：不存在帳號應失敗，並出現「帳號不存在」警告彈窗"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login("nonexistent_user_xyz", site_config.password)

        warning_title = page.locator("text=警告").first
        error_msg = page.locator("text=帳號不存在").first
        confirm_btn = page.locator("button:not(.toast-confirm-btn)", has_text="確定").first
        sh = get_screenshotter(page)
        if sh: sh.capture(warning_title, "verify_警告標題")
        if sh: sh.capture(error_msg, "verify_帳號不存在訊息")
        if sh: sh.capture(confirm_btn, "verify_確定按鈕")
        expect(warning_title).to_be_visible(timeout=5000)
        expect(error_msg).to_be_visible()
        expect(confirm_btn).to_be_visible()

    def test_login_empty_fields(self, page: Page, site_config):
        """RE-TC-004：空白帳號密碼時送出按鈕應為 disabled（client-side 驗證）

        與 RC 不同：RC 按鈕保持 enabled 由 server 拒絕；
        RE 在欄位空白時直接 disable button，不允許 click。
        斷言改為 disabled 狀態，截圖前先 scroll 進畫面以利 review 對照。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()

        login.login_btn.scroll_into_view_if_needed()
        sh = get_screenshotter(page)
        if sh: sh.capture(login.login_btn, "verify_送出按鈕_空白欄位disabled")
        if sh: sh.capture(login.username_input, "verify_帳號欄位仍可見")
        expect(login.login_btn).to_be_disabled(timeout=3000)
        expect(login.username_input).to_be_visible()


@pytest.mark.p0
@pytest.mark.re
@pytest.mark.home
class TestHomePage:
    """RE-TC-005 ~ RE-TC-007, RE-TC-023：首頁核心元素"""

    def test_home_page_loads(self, logged_in_page: Page, site_config):
        """RE-TC-005：登入後首頁正常載入"""
        home = HomePage(logged_in_page)
        home.verify_logged_in()

    def test_navigation_visible(self, logged_in_page: Page):
        """RE-TC-006：主要導覽列應顯示（真人/電子/捕魚）"""
        sh = get_screenshotter(logged_in_page)
        for nav_item in ["真人", "電子", "捕魚"]:
            el = logged_in_page.locator(f"text={nav_item}").first
            if sh: sh.capture(el, f"verify_導覽列_{nav_item}")
            expect(el).to_be_visible()

    def test_logout(self, logged_in_page: Page):
        """RE-TC-007：登入後可正常登出，右上角應出現「登入」按鈕"""
        home = HomePage(logged_in_page)
        home.logout()
        expect(home.login_btn).to_be_visible(timeout=5000)

    def test_login_form_elements_exist(self, page: Page, site_config):
        """RE-TC-023：登入 modal 元素存在（帳號/密碼輸入框/送出按鈕）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        sh = get_screenshotter(page)

        if sh: sh.capture(login.username_input, "verify_帳號欄位")
        if sh: sh.capture(login.password_input, "verify_密碼欄位")
        if sh: sh.capture(login.login_btn,      "verify_登入按鈕")
        expect(login.username_input).to_be_visible()
        expect(login.password_input).to_be_visible()
        expect(login.login_btn).to_be_visible()
