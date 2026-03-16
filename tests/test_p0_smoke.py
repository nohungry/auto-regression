"""
P0 Smoke Test
每次 Release 必跑，驗證核心功能正常
"""

import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.home_page import HomePage


class TestLogin:
    """TC-001 ~ TC-003：登入相關"""

    def test_login_success(self, page: Page, site_config):
        """TC-001：正常登入"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_wrong_password(self, page: Page, site_config):
        """TC-002：錯誤密碼登入應失敗"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login(site_config.username, "wrong_password_123")

        # 應出現錯誤提示（不應成功登入）
        error_msg = page.locator(
            "[class*='error'], [class*='toast'], .text-red, p:has-text('錯誤')"
        )
        expect(error_msg).to_be_visible(timeout=5000)

    def test_login_empty_fields(self, page: Page, site_config):
        """TC-003：空白帳號密碼不應登入成功"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()

        # 直接點登入按鈕（不填資料）
        login.login_btn.click()

        # 不應跳轉（仍在登入頁）
        expect(login.username_input).to_be_visible(timeout=3000)


class TestHomePage:
    """TC-004 ~ TC-005：首頁核心元素"""

    def test_home_page_loads(self, logged_in_page: Page, site_config):
        """TC-004：登入後首頁正常載入"""
        # 驗證帳號名稱顯示
        expect(
            logged_in_page.locator(f"text={site_config.username}")
        ).to_be_visible()

    def test_navigation_visible(self, logged_in_page: Page):
        """TC-005：主要導覽列應顯示"""
        # 驗證導覽列項目（真人、電子、捕魚）
        for nav_item in ["真人", "電子", "捕魚"]:
            expect(
                logged_in_page.locator(f"text={nav_item}").first
            ).to_be_visible()
