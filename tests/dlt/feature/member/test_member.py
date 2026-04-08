"""
會員功能測試（個人資料 / 收件匣）
WIN-MEMBER-001~004
"""

import pytest
from playwright.sync_api import Page, expect
from pages.dlt.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.member
class TestMember:
    """WIN-MEMBER-001~004：個人資料與收件匣功能驗證"""

    def test_personal_info_panel_opens(self, class_logged_in_page: Page, go_home):
        """WIN-MEMBER-001：點擊編輯圖示後，個人資料面板（會員帳號）出現"""
        page = class_logged_in_page
        home = HomePage(page)
        home.open_personal_info_dialog()
        panel_title = page.locator(".dialog-container .flex-1 p.mb-5.font-bold")
        expect(panel_title).to_have_text("會員帳號")

    def test_personal_info_shows_username(self, class_logged_in_page: Page, go_home, site_config):
        """WIN-MEMBER-002：個人資料面板顯示正確帳號名稱"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.open_personal_info_dialog()
        username_el = page.locator(".dialog-container p.text-text-light-main").first
        expect(username_el).to_have_text(site_config.username)
        if sh: sh.capture(username_el, "verify_個人資料帳號名稱")

    def test_personal_info_has_change_password(self, class_logged_in_page: Page, go_home):
        """WIN-MEMBER-003：個人資料面板有「修改密碼」按鈕"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.open_personal_info_dialog()
        change_pw_btn = page.locator(".dialog-container .flex-1 div.bg-secondary")
        expect(change_pw_btn).to_be_visible()
        expect(change_pw_btn).to_have_text("修改密碼")
        if sh: sh.capture(change_pw_btn, "verify_修改密碼按鈕")

    def test_inbox_panel_opens(self, class_logged_in_page: Page, go_home):
        """WIN-MEMBER-004：點擊會員訊息後，收件匣面板出現"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.open_inbox_dialog()
        panel_title = page.locator(".dialog-container .flex-1 p.mb-5.font-bold")
        expect(panel_title).to_have_text("會員訊息")
        if sh: sh.full_page("verify_收件匣面板")
        home.close_dialog()

    def test_betting_history_panel_opens(self, class_logged_in_page: Page, go_home):
        """WIN-MEMBER-005：點擊投注紀錄後，投注紀錄面板出現且含日期篩選與搜尋按鈕"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)
        home.open_betting_history_dialog()
        panel_title = page.locator(".dialog-container .flex-1 p.mb-5.font-bold")
        expect(panel_title).to_have_text("投注紀錄")
        # 日期篩選 tab（今日）可見
        today_tab = page.locator(".dialog-container .flex-1 p", has_text="今日").first
        expect(today_tab).to_be_visible()
        # 搜尋按鈕可見
        search_btn = page.locator(".dialog-container button.main-button")
        expect(search_btn).to_be_visible()
        if sh: sh.full_page("verify_投注紀錄面板")
        home.close_dialog()
