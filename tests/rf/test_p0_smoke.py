"""
RF P0 Smoke Test — 金爺娛樂城（rf / drf）
每次 Release 必跑，涵蓋核心健康度流程：登入、首頁載入、登出、登入表單可見性。

站台特性：
- 登入入口為 a.btn-login（<a> 非 button），點後導頁至 /Login 頁
- 送出後有多段 base-modal 確認彈窗（用戶協議*首次 + 登入成功*每次），需逐一點「確定」
- 已登入信號：.info_name 可見
- 登出：.loginInBox 下拉 → button.btn-logout
- 導覽按鈕（真人/電子/捕魚）為 button，文字也出現在遊戲卡，用 .first 取第一個

Flaky 標記（test_login_wrong_password / test_login_wrong_username）：
- RF 沒有 RC 的 MutationObserver，不需要同樣理由；
  但 dev 環境網路偶爾慢，base-modal 出現時序不穩，故各加 1 次 retry 吸收。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.rf.login_page import LoginPage
from pages.rf.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p0
@pytest.mark.rf
@pytest.mark.login
class TestLogin:
    """TC-001 ~ TC-004：登入相關"""

    def test_login_success(self, page: Page, site_config):
        """TC-001：正常登入，.info_name 可見且文字含登入帳號。"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_wrong_password(self, page: Page, site_config):
        """TC-002：正確帳號 + 錯誤密碼應失敗，出現 base-modal 錯誤彈窗。

        斷言策略：
        - p.alert-text 可見（base-modal 錯誤彈窗出現）
        - p.alert-text 文字含「密碼錯誤」（已實機驗證）

        注意：此 test 不呼叫 complete_login_modals()，保留錯誤彈窗供斷言。
        （原標 flaky：base-modal 時序不穩；LoginPage 改「等 modal 消失」後 CDP
        連跑 8 輪 0 flake，已移除 flaky 標記。）
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login(site_config.username, "wrong_password_123")

        alert = page.locator("p.alert-text")
        sh = get_screenshotter(page)
        if sh:
            sh.capture(alert, "verify_錯誤彈窗_密碼錯誤")
        expect(alert).to_be_visible(timeout=8000)
        expect(alert).to_contain_text("密碼錯誤")

    def test_login_wrong_username(self, page: Page, site_config):
        """TC-003：不存在帳號應失敗，出現 base-modal 錯誤彈窗。

        斷言策略：
        - p.alert-text 可見（base-modal 錯誤彈窗出現）
        - p.alert-text 文字含「帳號不存在」（已實機驗證 dev-rf 2026-06-17）

        注意：此 test 不呼叫 complete_login_modals()，保留錯誤彈窗供斷言。
        （原標 flaky：同 test_login_wrong_password，改「等 modal 消失」後穩定，已移除。）
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login("nonexistent_user_xyz", site_config.password)

        alert = page.locator("p.alert-text")
        sh = get_screenshotter(page)
        if sh:
            sh.capture(alert, "verify_錯誤彈窗_帳號不存在")
        expect(alert).to_be_visible(timeout=8000)
        expect(alert).to_contain_text("帳號不存在")

    def test_login_empty_fields(self, page: Page, site_config):
        """TC-004：空白帳號密碼送出後仍停在登入頁，#desktop-account 仍可見。"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()

        login.login_btn.scroll_into_view_if_needed()
        sh = get_screenshotter(page)
        if sh:
            sh.capture(login.login_btn, "click_送出登入_空白欄位")
        login.login_btn.click()

        if sh:
            sh.capture(login.username_input, "verify_仍在登入頁")
        expect(login.username_input).to_be_visible(timeout=3000)


@pytest.mark.p0
@pytest.mark.rf
@pytest.mark.home
class TestHomePage:
    """TC-005 ~ TC-008：首頁核心元素"""

    def test_home_page_loads(self, logged_in_page: Page, site_config):
        """TC-005：登入後首頁正常載入，.info_name 可見。"""
        home = HomePage(logged_in_page)
        home.verify_logged_in()

    def test_navigation_visible(self, logged_in_page: Page):
        """TC-006：主要導覽列應顯示（真人/電子/捕魚）。

        斷言策略：
        - 限縮在 nav.menu_nav 容器內的 button（避免命中首頁遊戲卡上的同名文字 → 假綠燈）
        - 驗證各 nav button 可見
        """
        home = HomePage(logged_in_page)
        sh = get_screenshotter(logged_in_page)
        for nav_item in ["真人", "電子", "捕魚"]:
            el = home.nav_menu.locator("button", has_text=nav_item).first
            el.scroll_into_view_if_needed()
            if sh:
                sh.capture(el, f"verify_導覽列_{nav_item}")
            expect(el).to_be_visible()

    def test_logout(self, logged_in_page: Page):
        """TC-007：登入後可正常登出，a.btn-login（登入/註冊）應重新出現。"""
        home = HomePage(logged_in_page)
        home.logout()
        expect(home.login_btn).to_be_visible(timeout=5000)

    def test_login_form_elements_exist(self, page: Page, site_config):
        """TC-008：/Login 頁表單元素存在（帳號欄/密碼欄/送出按鈕）。"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        sh = get_screenshotter(page)

        if sh:
            sh.capture(login.username_input, "verify_帳號欄位")
        if sh:
            sh.capture(login.password_input, "verify_密碼欄位")
        if sh:
            sh.capture(login.login_btn, "verify_登入按鈕")
        expect(login.username_input).to_be_visible()
        expect(login.password_input).to_be_visible()
        expect(login.login_btn).to_be_visible()
