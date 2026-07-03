"""
RC 側邊欄功能測試
遊戲明細彈窗、老吉公告彈窗、未登入時點擊跳出登入表單
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from pages.rc.login_page import LoginPage
from utils.dialog_helper import wait_loading_if_present
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.rc
class TestSidebarFeatures:
    """TC-021 ~ TC-022：側邊欄彈窗功能（已登入）"""

    def test_game_details_opens(self, class_logged_in_page: Page, go_home):
        """TC-021：遊戲明細彈窗可正常開啟"""
        page = class_logged_in_page
        page.locator(".sidebar-item.game-details").dispatch_event("click")
        dialog = page.locator(".dialog-container")
        sh = get_screenshotter(page)
        # 先等 dialog 可見再截圖，否則 capture 命中 0 元素（dialog 尚未 render）
        expect(dialog).to_be_visible(timeout=5000)
        if sh: sh.capture(dialog, "verify_遊戲明細彈窗開啟")

    def test_announcement_opens(self, class_logged_in_page: Page, go_home):
        """TC-022：老吉公告彈窗可正常開啟且有公告內容"""
        page = class_logged_in_page
        page.locator(".sidebar-item.announce").dispatch_event("click")
        wait_loading_if_present(page)
        dialog = page.locator(".dialog-container")
        sh = get_screenshotter(page)
        expect(dialog).to_be_visible(timeout=5000)
        if sh: sh.capture(dialog, "verify_公告彈窗開啟")
        expect(dialog).to_contain_text("公告")


@pytest.mark.p1
@pytest.mark.rc
@pytest.mark.login
class TestUnauthenticatedSidebar:
    """TC-020：未登入時的側邊欄行為"""

    def test_sidebar_triggers_login(self, page: Page, site_config):
        """TC-020：未登入時點側邊欄個人資訊應跳出登入表單。

        Hydration dead zone：sidebar `@click` handler 在 page open 後約 2 秒才綁定，
        pytest fresh context 在 hydration 完成前 dispatch click 會 no-op（與
        `pages/rc/login_page.py::open_login_form` 同症狀，同樣用 retry loop 處理）。
        2026-05-19 probe 確認 root cause。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        sidebar_user = page.locator(".sidebar-item.user")

        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            sidebar_user.dispatch_event("click")
            try:
                login.username_input.wait_for(state="visible", timeout=1500)
                break  # modal opened
            except PlaywrightTimeoutError:
                if attempt == max_attempts:
                    raise

        wait_loading_if_present(page)
        sh = get_screenshotter(page)
        if sh: sh.capture(login.username_input, "verify_登入表單出現")
        expect(login.username_input).to_be_visible(timeout=5000)
