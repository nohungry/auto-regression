"""
DRC 會員功能測試
個人資訊彈窗、站內信彈窗
"""

import pytest
from playwright.sync_api import Page, expect
from utils.dialog_helper import wait_loading_if_present
from utils.screenshot_helper import get_screenshotter


def _open_sidebar(page: Page, sidebar_class: str):
    """
    觸發 sidebar 項目點擊。
    sidebar 容器 CSS width=0，必須 dispatch_event 直接觸發 DOM 事件。
    """
    page.locator(f".sidebar-item.{sidebar_class}").dispatch_event("click")
    wait_loading_if_present(page)


def _close_dialog(page: Page):
    """關閉彈窗（X 按鈕）"""
    close_btn = page.locator(".close-wrap")
    close_btn.scroll_into_view_if_needed()
    sh = get_screenshotter(page)
    if sh: sh.capture(close_btn, "click_關閉彈窗")
    close_btn.click()
    expect(page.locator(".dialog-container")).not_to_be_visible(timeout=5000)


@pytest.mark.p1
@pytest.mark.member
class TestPersonalInfo:
    """TC-011 ~ TC-012：個人資訊彈窗"""

    def test_personal_info_opens(self, class_logged_in_page: Page, go_home, site_config):
        """TC-011：個人資訊彈窗可正常開啟，帳號欄位顯示正確用戶名"""
        page = class_logged_in_page
        _open_sidebar(page, "user")
        dialog = page.locator(".dialog-container")
        expect(dialog).to_be_visible(timeout=5000)
        sh = get_screenshotter(page)
        if sh: sh.capture(dialog, "verify_個人資訊彈窗開啟")

        username_field = page.locator(".dialog-container input[disabled]").first
        expect(username_field).to_have_value(site_config.username)
        if sh: sh.capture(username_field, "verify_帳號欄位顯示正確")

    def test_personal_info_closes(self, class_logged_in_page: Page, go_home):
        """TC-012：個人資訊彈窗可正常關閉"""
        page = class_logged_in_page
        _open_sidebar(page, "user")
        expect(page.locator(".dialog-container")).to_be_visible(timeout=5000)
        _close_dialog(page)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_個人資訊彈窗已關閉")


@pytest.mark.p1
@pytest.mark.member
class TestInbox:
    """TC-013 ~ TC-014：站內信彈窗"""

    def test_inbox_opens(self, class_logged_in_page: Page, go_home):
        """TC-013：站內信彈窗可正常開啟"""
        page = class_logged_in_page
        _open_sidebar(page, "mail")
        dialog = page.locator(".dialog-container")
        expect(dialog).to_be_visible(timeout=5000)
        expect(dialog).to_contain_text("站內信")
        sh = get_screenshotter(page)
        if sh: sh.capture(dialog, "verify_站內信彈窗開啟")

    def test_inbox_closes(self, class_logged_in_page: Page, go_home):
        """TC-014：站內信彈窗可正常關閉"""
        page = class_logged_in_page
        _open_sidebar(page, "mail")
        expect(page.locator(".dialog-container")).to_be_visible(timeout=5000)
        _close_dialog(page)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_站內信彈窗已關閉")
