"""
P0 Smoke Test
每次 Release 必跑，驗證核心功能正常
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.drc.login_page import LoginPage
from pages.drc.home_page import HomePage
from utils.dialog_helper import wait_loading_if_present
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p0
@pytest.mark.login
class TestLogin:
    """TC-001 ~ TC-004：登入相關"""

    def test_login_success(self, page: Page, site_config):
        """TC-001：正常登入"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_wrong_password(self, page: Page, site_config):
        """TC-002：正確帳號 + 錯誤密碼應失敗，並出現「密碼錯誤」警告彈窗"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login(site_config.username, "wrong_password_123")

        # 確定按鈕出現
        toast_btn = page.locator("button.toast-confirm-btn")
        expect(toast_btn).to_be_visible(timeout=5000)
        # 驗證彈窗訊息為「密碼錯誤」
        error_msg = page.locator("p", has_text="密碼錯誤")
        expect(error_msg).to_be_visible()
        sh = get_screenshotter(page)
        if sh: sh.capture(error_msg, "verify_密碼錯誤訊息")
        if sh: sh.capture(toast_btn, "verify_確定按鈕")

    def test_login_wrong_username(self, page: Page, site_config):
        """TC-003：不存在帳號應失敗，並出現「帳號不存在」警告彈窗"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login("nonexistent_user_xyz", site_config.password)

        # 確定按鈕出現
        toast_btn = page.locator("button.toast-confirm-btn")
        expect(toast_btn).to_be_visible(timeout=5000)
        # 驗證彈窗訊息為「帳號不存在」
        error_msg = page.locator("p", has_text="帳號不存在")
        expect(error_msg).to_be_visible()
        sh = get_screenshotter(page)
        if sh: sh.capture(error_msg, "verify_帳號不存在訊息")
        if sh: sh.capture(toast_btn, "verify_確定按鈕")

    def test_login_empty_fields(self, page: Page, site_config):
        """TC-004：空白帳號密碼不應登入成功"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()

        # 直接點登入按鈕（不填資料）
        login.login_btn.scroll_into_view_if_needed()
        sh = get_screenshotter(page)
        if sh: sh.capture(login.login_btn, "click_送出登入_空白欄位")
        login.login_btn.click()

        # 不應跳轉（仍在登入頁）
        expect(login.username_input).to_be_visible(timeout=3000)
        if sh: sh.capture(login.username_input, "verify_仍在登入頁")


@pytest.mark.p0
@pytest.mark.home
class TestHomePage:
    """TC-005 ~ TC-007, TC-023：首頁核心元素"""

    def test_home_page_loads(self, logged_in_page: Page, site_config):
        """TC-005：登入後首頁正常載入"""
        home = HomePage(logged_in_page)
        home.verify_login_success(site_config.username)

    def test_navigation_visible(self, logged_in_page: Page):
        """TC-006：主要導覽列應顯示"""
        sh = get_screenshotter(logged_in_page)
        # 驗證導覽列項目（真人、電子、捕魚）
        for nav_item in ["真人", "電子", "捕魚"]:
            el = logged_in_page.locator(f"text={nav_item}").first
            expect(el).to_be_visible()
            if sh: sh.capture(el, f"verify_導覽列_{nav_item}")

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

        expect(login.username_input).to_be_visible()
        expect(login.password_input).to_be_visible()
        expect(login.login_btn).to_be_visible()
        if sh: sh.capture(login.username_input, "verify_帳號欄位")
        if sh: sh.capture(login.password_input, "verify_密碼欄位")
        if sh: sh.capture(login.login_btn,      "verify_登入按鈕")


@pytest.mark.p0
class TestPersonalInfo:
    """TC-011 ~ TC-012：個人資訊彈窗"""

    def test_personal_info_opens(self, logged_in_page: Page, site_config):
        """TC-011：個人資訊彈窗可正常開啟，帳號欄位顯示正確用戶名"""
        # sidebar 容器 CSS width=0，dispatch_event 直接觸發 DOM 事件；點擊後有 loading
        logged_in_page.locator(".sidebar-item.user").dispatch_event("click")
        wait_loading_if_present(logged_in_page)
        dialog = logged_in_page.locator(".dialog-container")
        expect(dialog).to_be_visible(timeout=5000)
        sh = get_screenshotter(logged_in_page)
        if sh: sh.capture(dialog, "verify_個人資訊彈窗開啟")
        username_field = logged_in_page.locator(".dialog-container input[disabled]").first
        expect(username_field).to_have_value(site_config.username)
        if sh: sh.capture(username_field, "verify_帳號欄位顯示正確")

    def test_personal_info_closes(self, logged_in_page: Page):
        """TC-012：個人資訊彈窗可正常關閉（X 按鈕）"""
        logged_in_page.locator(".sidebar-item.user").dispatch_event("click")
        wait_loading_if_present(logged_in_page)
        expect(logged_in_page.locator(".dialog-container")).to_be_visible(timeout=5000)
        close_btn = logged_in_page.locator(".close-wrap")
        close_btn.scroll_into_view_if_needed()
        sh = get_screenshotter(logged_in_page)
        if sh: sh.capture(close_btn, "click_關閉彈窗")
        close_btn.click()
        expect(logged_in_page.locator(".dialog-container")).not_to_be_visible(timeout=5000)
        if sh: sh.full_page("verify_個人資訊彈窗已關閉")


@pytest.mark.p0
class TestInbox:
    """TC-013 ~ TC-014：站內信彈窗"""

    def test_inbox_opens(self, logged_in_page: Page):
        """TC-013：站內信彈窗可正常開啟"""
        # sidebar 容器 CSS width=0，dispatch_event 直接觸發 DOM 事件
        logged_in_page.locator(".sidebar-item.mail").dispatch_event("click")
        wait_loading_if_present(logged_in_page)
        dialog = logged_in_page.locator(".dialog-container")
        expect(dialog).to_be_visible(timeout=5000)
        expect(dialog).to_contain_text("站內信")
        sh = get_screenshotter(logged_in_page)
        if sh: sh.capture(dialog, "verify_站內信彈窗開啟")

    def test_inbox_closes(self, logged_in_page: Page):
        """TC-014：站內信彈窗可正常關閉"""
        logged_in_page.locator(".sidebar-item.mail").dispatch_event("click")
        wait_loading_if_present(logged_in_page)
        expect(logged_in_page.locator(".dialog-container")).to_be_visible(timeout=5000)
        close_btn = logged_in_page.locator(".close-wrap")
        close_btn.scroll_into_view_if_needed()
        sh = get_screenshotter(logged_in_page)
        if sh: sh.capture(close_btn, "click_關閉彈窗")
        close_btn.click()
        expect(logged_in_page.locator(".dialog-container")).not_to_be_visible(timeout=5000)
        if sh: sh.full_page("verify_站內信彈窗已關閉")


@pytest.mark.p0
class TestCasinoPage:
    """TC-015：真人頁廳館"""

    def test_casino_halls_visible(self, logged_in_page: Page):
        """TC-015：真人頁顯示所有廳館（T9真人、RC真人、DG真人、MT真人、歐博）"""
        home = HomePage(logged_in_page)
        home.click_nav_item("真人")
        sh = get_screenshotter(logged_in_page)
        for hall in ["T9真人", "RC真人", "DG真人", "MT真人", "歐博"]:
            # sidebar 的廳館文字使用 text-black，排除後取廳館卡片內的可見節點
            el = logged_in_page.locator("p:not(.text-black)", has_text=hall).first
            expect(el).to_be_visible(timeout=8000)
            el.scroll_into_view_if_needed()
            if sh: sh.capture(el, f"verify_廳館_{hall}")
        if sh: sh.full_page("verify_所有廳館卡片_全頁")


@pytest.mark.p0
@pytest.mark.home
class TestHomePageSections:
    """TC-016 ~ TC-019：首頁各區塊"""

    def test_hot_games_section(self, logged_in_page: Page):
        """TC-016：首頁顯示「熱門遊戲」區塊且有遊戲卡片"""
        sh = get_screenshotter(logged_in_page)
        title = logged_in_page.locator("text=熱門遊戲").first
        expect(title).to_be_visible()
        if sh: sh.capture(title, "verify_熱門遊戲標題")
        grid = logged_in_page.locator(".mt-d-20.grid").first
        expect(grid).to_be_visible()
        grid.scroll_into_view_if_needed()
        if sh: sh.capture(grid, "verify_遊戲卡片區塊")
        if sh: sh.full_page("verify_遊戲卡片區塊_全頁")

    def test_new_games_section(self, logged_in_page: Page):
        """TC-017：首頁顯示「最新遊戲」區塊且有遊戲卡片"""
        sh = get_screenshotter(logged_in_page)
        # 熱門/最新共用同一個 grid，點 tab 切換後確認有卡片
        tab = logged_in_page.locator("text=最新遊戲").first
        tab.scroll_into_view_if_needed()
        if sh: sh.capture(tab, "click_最新遊戲Tab")
        tab.click()
        grid = logged_in_page.locator(".mt-d-20.grid").first
        expect(grid).to_be_visible()
        # tab 切換後 grid 重繪，用 evaluate 捲動視窗避免操作不穩定的元素
        logged_in_page.evaluate("window.scrollBy(0, 400)")
        if sh: sh.capture(grid, "verify_最新遊戲卡片區塊")
        if sh: sh.full_page("verify_最新遊戲卡片區塊_全頁")

    def test_announcement_marquee(self, logged_in_page: Page):
        """TC-018：首頁公告跑馬燈有內容顯示"""
        # 多個 p.h-full 存在，取第一個含公告文字的
        marquee = logged_in_page.locator("p.h-full").first
        expect(marquee).to_be_visible()
        expect(marquee).to_contain_text("公告")
        sh = get_screenshotter(logged_in_page)
        if sh: sh.capture(marquee, "verify_公告跑馬燈有內容")

    def test_balance_visible(self, logged_in_page: Page):
        """TC-019：登入後右上角餘額數字顯示（非空白）"""
        balance = logged_in_page.locator(".coin-wrap-bg span")
        expect(balance).to_be_visible()
        sh = get_screenshotter(logged_in_page)
        if sh: sh.capture(balance, "verify_餘額數字顯示")


@pytest.mark.p0
class TestUnauthenticated:
    """TC-020：未登入功能"""

    def test_sidebar_triggers_login(self, page: Page, site_config):
        """TC-020：未登入時點側邊欄個人資訊應跳出登入表單"""
        login = LoginPage(page, site_config.url)
        login.goto()
        # sidebar 容器 CSS width=0，dispatch_event 直接觸發 DOM 事件
        page.locator(".sidebar-item.user").dispatch_event("click")
        wait_loading_if_present(page)
        expect(login.username_input).to_be_visible(timeout=5000)
        sh = get_screenshotter(page)
        if sh: sh.capture(login.username_input, "verify_登入表單出現")


@pytest.mark.p0
class TestSidebarFeatures:
    """TC-021 ~ TC-022：側邊欄彈窗功能"""

    def test_game_details_opens(self, logged_in_page: Page):
        """TC-021：遊戲明細彈窗可正常開啟"""
        # sidebar 容器 CSS width=0，dispatch_event 直接觸發 DOM 事件
        logged_in_page.locator(".sidebar-item.game-details").dispatch_event("click")
        dialog = logged_in_page.locator(".dialog-container")
        expect(dialog).to_be_visible(timeout=5000)
        sh = get_screenshotter(logged_in_page)
        if sh: sh.capture(dialog, "verify_遊戲明細彈窗開啟")

    def test_announcement_opens(self, logged_in_page: Page):
        """TC-022：老吉公告彈窗可正常開啟且有公告內容"""
        logged_in_page.locator(".sidebar-item.announce").dispatch_event("click")
        wait_loading_if_present(logged_in_page)
        dialog = logged_in_page.locator(".dialog-container")
        expect(dialog).to_be_visible(timeout=5000)
        expect(dialog).to_contain_text("公告")
        sh = get_screenshotter(logged_in_page)
        if sh: sh.capture(dialog, "verify_公告彈窗開啟")


@pytest.mark.p0
class TestNavigation:
    """TC-008 ~ TC-010：導覽列分類頁跳轉"""

    @pytest.mark.parametrize("nav_item,expected_path", [
        ("真人", "/Categories/casino"),
        ("電子", "/Categories/slots"),
        ("捕魚", "/Categories/fishing"),
    ])
    def test_nav_to_category(self, logged_in_page: Page, nav_item, expected_path):
        """TC-008/009/010：點擊導覽列項目應跳轉至對應分類頁"""
        home = HomePage(logged_in_page)
        home.click_nav_item(nav_item)
        expect(logged_in_page).to_have_url(re.compile(re.escape(expected_path)), timeout=8000)
        sh = get_screenshotter(logged_in_page)
        if sh: sh.full_page(f"verify_已跳轉至_{nav_item}分類頁")
