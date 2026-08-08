"""
RE 側邊欄功能測試 (BeWin)
遊戲明細彈窗、BeWin 公告彈窗、未登入時點擊跳出登入表單
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from pages.factory import get_login_page_class
from utils.dialog_helper import wait_loading_if_present
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("re")


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
        # 先等 dialog 可見再截圖，否則 capture 命中 0 元素（dialog 尚未 render）
        expect(dialog).to_be_visible(timeout=5000)
        if sh: sh.capture(dialog, "verify_遊戲明細彈窗開啟")

    def test_announcement_opens(self, class_logged_in_page: Page, go_home):
        """RE-TC-022：BeWin 公告彈窗可正常開啟且有公告內容"""
        page = class_logged_in_page
        page.locator(".sidebar-item.announce").dispatch_event("click")
        wait_loading_if_present(page)
        dialog = page.locator(".dialog-container")
        sh = get_screenshotter(page)
        expect(dialog).to_be_visible(timeout=5000)
        if sh: sh.capture(dialog, "verify_公告彈窗開啟")
        expect(dialog).to_contain_text("公告")


@pytest.mark.p1
@pytest.mark.re
@pytest.mark.login
class TestUnauthenticatedSidebar:
    """RE-TC-020：未登入時的側邊欄行為"""

    def test_sidebar_triggers_login(self, page: Page, site_config):
        """RE-TC-020：未登入時點側邊欄個人資訊應跳出 /login 頁

        Hydration race：Vue handler 綁定可能延遲 1~2s，dispatch_event 太早會無事發生。
        retry click 直到 URL 變 /login（或 5 次後 fail）。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        sidebar_user = page.locator(".sidebar-item.user")
        sidebar_user.wait_for(state="attached", timeout=8000)
        sh = get_screenshotter(page)
        # RE sidebar 為 CSS width=0 隱藏（bbox 恆在視窗外）→ 整頁截圖呈現實際狀態，紅框無意義
        if sh: sh.full_page("click_側邊欄個人資訊")
        for _ in range(5):
            sidebar_user.dispatch_event("click")
            try:
                page.wait_for_url(lambda url: "/login" in url, timeout=2000)
                break
            except PlaywrightTimeoutError:
                continue
        else:
            raise AssertionError("sidebar.user click did not navigate to /login after 5 retries")
        wait_loading_if_present(page)
        if sh: sh.capture(login.username_input, "verify_登入表單出現")
        expect(login.username_input).to_be_visible(timeout=5000)
