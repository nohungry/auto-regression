"""
DRC 側邊欄功能測試
遊戲明細彈窗、老吉公告彈窗、未登入時點擊跳出登入表單
"""

import pytest
from playwright.sync_api import Page, expect
from pages.drc.login_page import LoginPage
from utils.dialog_helper import wait_loading_if_present
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
class TestSidebarFeatures:
    """TC-021 ~ TC-022：側邊欄彈窗功能（已登入）"""

    def test_game_details_opens(self, class_logged_in_page: Page, go_home):
        """TC-021：遊戲明細彈窗可正常開啟"""
        page = class_logged_in_page
        page.locator(".sidebar-item.game-details").dispatch_event("click")
        dialog = page.locator(".dialog-container")
        expect(dialog).to_be_visible(timeout=5000)
        sh = get_screenshotter(page)
        if sh: sh.capture(dialog, "verify_遊戲明細彈窗開啟")

    def test_announcement_opens(self, class_logged_in_page: Page, go_home):
        """TC-022：老吉公告彈窗可正常開啟且有公告內容"""
        page = class_logged_in_page
        page.locator(".sidebar-item.announce").dispatch_event("click")
        wait_loading_if_present(page)
        dialog = page.locator(".dialog-container")
        expect(dialog).to_be_visible(timeout=5000)
        expect(dialog).to_contain_text("公告")
        sh = get_screenshotter(page)
        if sh: sh.capture(dialog, "verify_公告彈窗開啟")


@pytest.mark.p1
@pytest.mark.login
class TestUnauthenticatedSidebar:
    """TC-020：未登入時的側邊欄行為"""

    def test_sidebar_triggers_login(self, page: Page, site_config):
        """TC-020：未登入時點側邊欄個人資訊應跳出登入表單"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.locator(".sidebar-item.user").dispatch_event("click")
        wait_loading_if_present(page)
        expect(login.username_input).to_be_visible(timeout=5000)
        sh = get_screenshotter(page)
        if sh: sh.capture(login.username_input, "verify_登入表單出現")
