"""
RE 側邊欄功能測試 (BeWin)
遊戲明細彈窗、BeWin 公告彈窗、未登入時點擊跳出登入表單
"""

import pytest
from playwright.sync_api import Page, expect
from pages.re.login_page import LoginPage
from utils.dialog_helper import wait_loading_if_present
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.re
class TestSidebarFeatures:
    """RE-TC-021 ~ RE-TC-022：側邊欄彈窗功能（已登入）"""

    def test_game_details_opens(self, class_logged_in_page: Page, go_home):
        """RE-TC-021：遊戲明細彈窗可正常開啟"""
        page = class_logged_in_page
        page.locator(".sidebar-item.game-details").dispatch_event("click")
        dialog = page.locator(".dialog-container")
        sh = get_screenshotter(page)
        if sh: sh.capture(dialog, "verify_遊戲明細彈窗開啟")
        expect(dialog).to_be_visible(timeout=5000)

    def test_announcement_opens(self, class_logged_in_page: Page, go_home):
        """RE-TC-022：BeWin 公告彈窗可正常開啟且有公告內容"""
        page = class_logged_in_page
        page.locator(".sidebar-item.announce").dispatch_event("click")
        wait_loading_if_present(page)
        dialog = page.locator(".dialog-container")
        sh = get_screenshotter(page)
        if sh: sh.capture(dialog, "verify_公告彈窗開啟")
        expect(dialog).to_be_visible(timeout=5000)
        expect(dialog).to_contain_text("公告")


@pytest.mark.p1
@pytest.mark.re
@pytest.mark.login
class TestUnauthenticatedSidebar:
    """RE-TC-020：未登入時的側邊欄行為"""

    @pytest.mark.xfail(
        strict=True,
        reason="dev-re 未實作「未登入點 sidebar 觸發登入表單」UX（點擊無反應）；產品補上後此 xfail 會 XPASS 守門。比照 rd 同款處理。",
    )
    def test_sidebar_triggers_login(self, page: Page, site_config):
        """RE-TC-020：未登入時點側邊欄個人資訊應跳出登入表單（**期望實作**）

        [2026-06-12] dev-re 點 sidebar 後不跳登入表單，與 rd 同款 UX 缺漏，
        改用 xfail(strict=True) 守門：產品補上此 UX → XPASS → strict 觸發 fail 提醒移除 xfail。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.locator(".sidebar-item.user").dispatch_event("click")
        wait_loading_if_present(page)
        sh = get_screenshotter(page)
        if sh: sh.capture(login.username_input, "verify_登入表單出現")
        expect(login.username_input).to_be_visible(timeout=5000)
