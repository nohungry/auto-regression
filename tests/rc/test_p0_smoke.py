"""
RC P0 Smoke Test
每次 Release 必跑，只保留核心健康度流程（登入、首頁載入、登出、登入表單可見性）。

功能型測試已遷移：
- 個人資訊 / 站內信  → tests/rc/feature/member/test_member.py
- 首頁區塊（熱門/最新/公告/餘額）→ tests/rc/feature/home_sections/test_home_sections.py
- 側邊欄彈窗（遊戲明細/老吉公告 / 未登入跳登入）→ tests/rc/feature/sidebar/test_sidebar.py
- 真人廳館顯示             → tests/rc/feature/navigation/test_navigation.py
- 分類頁跳轉（真人/電子/捕魚）→ tests/rc/feature/navigation/test_navigation.py
"""

import pytest
from playwright.sync_api import Page, expect
from pages.rc.login_page import LoginPage
from pages.rc.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p0
@pytest.mark.rc
@pytest.mark.login
class TestLogin:
    """TC-001 ~ TC-004：登入相關"""

    def test_login_success(self, page: Page, site_config):
        """TC-001：正常登入"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    @pytest.mark.flaky(reruns=1, reruns_delay=5)
    def test_login_wrong_password(self, page: Page, site_config):
        """TC-002：正確帳號 + 錯誤密碼應失敗，並出現「密碼錯誤」警告彈窗

        Flaky 標記原因：global MutationObserver（conftest.py 注入）會秒關所有
        toast-confirm-btn，偶爾在 assert visible 前已關閉。retry 1 次吸收。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login(site_config.username, "wrong_password_123")

        toast_btn = page.locator("button.toast-confirm-btn")
        error_msg = page.locator("p", has_text="密碼錯誤")
        sh = get_screenshotter(page)
        if sh: sh.capture(toast_btn, "verify_確定按鈕")
        if sh: sh.capture(error_msg, "verify_密碼錯誤訊息")
        expect(toast_btn).to_be_visible(timeout=5000)
        expect(error_msg).to_be_visible()

    @pytest.mark.flaky(reruns=1, reruns_delay=5)
    def test_login_wrong_username(self, page: Page, site_config):
        """TC-003：不存在帳號應失敗，並出現「帳號不存在」警告彈窗

        Flaky 標記原因：同 test_login_wrong_password — observer 秒關 toast race。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login("nonexistent_user_xyz", site_config.password)

        toast_btn = page.locator("button.toast-confirm-btn")
        error_msg = page.locator("p", has_text="帳號不存在")
        sh = get_screenshotter(page)
        if sh: sh.capture(toast_btn, "verify_確定按鈕")
        if sh: sh.capture(error_msg, "verify_帳號不存在訊息")
        expect(toast_btn).to_be_visible(timeout=5000)
        expect(error_msg).to_be_visible()

    def test_login_empty_fields(self, page: Page, site_config):
        """TC-004：空白帳號密碼不應登入成功"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()

        login.login_btn.scroll_into_view_if_needed()
        sh = get_screenshotter(page)
        if sh: sh.capture(login.login_btn, "click_送出登入_空白欄位")
        login.login_btn.click()

        if sh: sh.capture(login.username_input, "verify_仍在登入頁")
        expect(login.username_input).to_be_visible(timeout=3000)


@pytest.mark.p0
@pytest.mark.rc
@pytest.mark.home
class TestHomePage:
    """TC-005 ~ TC-007, TC-023：首頁核心元素"""

    def test_home_page_loads(self, logged_in_page: Page, site_config):
        """TC-005：登入後首頁正常載入"""
        home = HomePage(logged_in_page)
        home.verify_logged_in()

    def test_navigation_visible(self, logged_in_page: Page):
        """TC-006：主要導覽列應顯示（真人/電子/捕魚）"""
        sh = get_screenshotter(logged_in_page)
        for nav_item in ["真人", "電子", "捕魚"]:
            el = logged_in_page.locator(f"text={nav_item}").first
            if sh: sh.capture(el, f"verify_導覽列_{nav_item}")
            expect(el).to_be_visible()

    def test_logout(self, logged_in_page: Page):
        """TC-007：登入後可正常登出，右上角應出現「登入」按鈕"""
        home = HomePage(logged_in_page)
        home.logout()
        expect(home.login_btn).to_be_visible(timeout=5000)

    def test_login_form_elements_exist(self, page: Page, site_config):
        """TC-023：登入 modal 元素存在（帳號/密碼輸入框/送出按鈕）"""
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


@pytest.mark.p0
@pytest.mark.rc
def test_DUMMY_slack_failure_demo_REMOVE():
    """[暫時 demo] 故意失敗以端到端驗證 CI 失敗 Slack 通知。
    驗證後即刪（此 branch 不 merge、不碰 main）。"""
    assert False, "intentional failure — Slack notification end-to-end demo"
