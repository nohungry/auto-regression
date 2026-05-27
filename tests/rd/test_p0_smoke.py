"""
RD P0 Smoke Test (狗狗娛樂城)
每次 Release 必跑，只保留核心健康度流程（登入、首頁載入、登出、登錄表單可見性）。

RD 站特性：
- 文案用「登錄」（不是「登入」）
- navbar 不顯示 username/avatar（登入信號為「登錄」按鈕消失）
- dialog-mask 蓋板廣告會攔截 pointer events（用 dispatch_event 繞過）
"""

import pytest
from playwright.sync_api import Page, expect
from pages.rd.login_page import LoginPage
from pages.rd.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p0
@pytest.mark.rd
@pytest.mark.login
class TestLogin:
    """RD-TC-001 ~ RD-TC-004：登入相關"""

    def test_login_success(self, page: Page, site_config):
        """RD-TC-001：正常登入"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_wrong_password(self, page: Page, site_config):
        """RD-TC-002：正確帳號 + 錯誤密碼應失敗

        RD 錯誤彈窗結構待 probe；先做最寬鬆的斷言：
        - 登入後仍應在 login modal 上（username_input 仍 visible）
        - 不應出現「登入成功」信號（navbar「登錄」按鈕仍 visible）
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login(site_config.username, "wrong_password_123")

        home = HomePage(page)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_密碼錯誤_未登入")
        # 登入失敗：「登錄」按鈕仍應 visible
        expect(home.login_btn).to_be_visible(timeout=5000)

    def test_login_wrong_username(self, page: Page, site_config):
        """RD-TC-003：不存在帳號應失敗"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login("nonexistent_user_xyz", site_config.password)

        home = HomePage(page)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_帳號不存在_未登入")
        expect(home.login_btn).to_be_visible(timeout=5000)

    def test_login_empty_fields(self, page: Page, site_config):
        """RD-TC-004：空白帳號密碼不應登入成功

        實測：RD button 在空白欄位時仍 enabled（與 RE 不同），點擊後仍停留登入頁。
        與 RC 同模式：斷言改為「點擊後仍在登入頁」（username_input 仍可見）。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()

        sh = get_screenshotter(page)
        if sh: sh.capture(login.login_btn, "click_送出登錄_空白欄位")
        login.login_btn.dispatch_event("click")

        if sh: sh.capture(login.username_input, "verify_仍在登錄頁")
        expect(login.username_input).to_be_visible(timeout=3000)


@pytest.mark.p0
@pytest.mark.rd
@pytest.mark.home
class TestHomePage:
    """RD-TC-005 ~ RD-TC-007, RD-TC-023：首頁核心元素"""

    def test_home_page_loads(self, logged_in_page: Page, site_config):
        """RD-TC-005：登入後首頁正常載入"""
        home = HomePage(logged_in_page)
        home.verify_logged_in()

    def test_navigation_visible(self, logged_in_page: Page):
        """RD-TC-006：主要導覽列應顯示（真人/電子/捕魚）"""
        sh = get_screenshotter(logged_in_page)
        for nav_item in ["真人", "電子", "捕魚"]:
            el = logged_in_page.locator(f"text={nav_item}").first
            if sh: sh.capture(el, f"verify_導覽列_{nav_item}")
            expect(el).to_be_visible()

    def test_logout(self, logged_in_page: Page):
        """RD-TC-007：登入後可正常登出

        登出流程：點「個人資訊」menu 開啟面板 → 點面板內「登出」按鈕 →
        驗證右上角「登錄」按鈕重新出現。
        """
        home = HomePage(logged_in_page)
        home.logout()
        expect(home.login_btn).to_be_visible(timeout=5000)

    def test_login_form_elements_exist(self, page: Page, site_config):
        """RD-TC-023：登錄 modal 元素存在（帳號/密碼輸入框/送出按鈕）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        sh = get_screenshotter(page)

        if sh: sh.capture(login.username_input, "verify_帳號欄位")
        if sh: sh.capture(login.password_input, "verify_密碼欄位")
        if sh: sh.capture(login.login_btn,      "verify_登錄按鈕")
        expect(login.username_input).to_be_visible()
        expect(login.password_input).to_be_visible()
        expect(login.login_btn).to_be_visible()
