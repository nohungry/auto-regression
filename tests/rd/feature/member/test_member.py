"""
RD 會員功能測試（個人資訊面板開/關 + 站內信切換）— 狗狗娛樂城

與 RC 結構差異：
- RD 個人資訊與站內信為「同一 dialog 面板」，不是兩個獨立 dialog：
  - 點 sidebar「個人資訊」開啟面板，預設顯示帳號資訊 + 站內信列表 + 操作按鈕
  - 點 sidebar「站內信」也會打開同一面板（focus 在 inbox 區塊）
- 因此測 4 項：開個人資訊 / 關個人資訊 / 站內信入口可點 / 站內信 tabs（全部/已讀/未讀）顯示
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("rd")


def _panel_open_signal(page: Page):
    """個人資訊/站內信面板開啟的信號 locator：面板內「登出」按鈕（已登入才有，且只在面板內出現）"""
    return page.locator('button.main-btn', has_text="登出").first


def _close_panel(page: Page):
    """關閉個人資訊面板：找該面板的 `.close-wrap`（filter visible），dispatch_event"""
    sh = get_screenshotter(page)
    # 多個 .close-wrap 存在於 DOM（登入 modal / 公告彈窗 / 個人資訊面板等），需 filter 可見
    close_btns = page.locator(".close-wrap")
    visible_close = None
    for i in range(close_btns.count()):
        btn = close_btns.nth(i)
        if btn.is_visible():
            visible_close = btn
            break
    assert visible_close is not None, "找不到可見的 close-wrap"
    if sh: sh.capture(visible_close, "click_關閉面板")
    visible_close.dispatch_event("click")
    page.wait_for_timeout(800)


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.member
class TestPersonalInfo:
    """RD-MEMBER-001 ~ 002：個人資訊面板開/關"""

    def test_personal_info_opens(self, class_logged_in_page: Page, go_home, site_config):
        """RD-MEMBER-001：點 sidebar「個人資訊」開啟面板，顯示帳號 username"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        home = HomePage(page)

        home.open_user_dropdown()  # POM 已封裝 dispatch_event + dialog-mask 處理

        # 驗證面板可見：登出按鈕只在面板內出現（POM open_user_dropdown 已驗，這裡再強化截圖）
        signal = _panel_open_signal(page)
        expect(signal).to_be_visible(timeout=5000)
        if sh: sh.full_page("verify_個人資訊面板開啟")

        # 帳號顯示：「會員帳戶：<RD 會員帳號>」格式（在面板的 dialog-container 內）
        username_row = page.locator(".dialog-container", has_text=f"會員帳戶：{site_config.username}").first
        expect(username_row).to_be_visible(timeout=5000)
        if sh: sh.capture(username_row, f"verify_帳號顯示_{site_config.username}")

    def test_personal_info_closes(self, class_logged_in_page: Page, go_home):
        """RD-MEMBER-002：個人資訊面板關閉後登出按鈕不再可見"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        home = HomePage(page)

        home.open_user_dropdown()
        signal = _panel_open_signal(page)
        expect(signal).to_be_visible(timeout=5000)

        _close_panel(page)

        # 關閉後 logout 按鈕不應再可見
        expect(signal).not_to_be_visible(timeout=5000)
        if sh: sh.full_page("verify_個人資訊面板已關閉")


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.member
class TestInbox:
    """RD-MEMBER-003 ~ 004：站內信入口 + tabs"""

    def test_inbox_sidebar_opens_panel(self, class_logged_in_page: Page, go_home):
        """RD-MEMBER-003：點 sidebar「站內信」開啟同一個面板（用面板內登出按鈕當信號）"""
        page = class_logged_in_page
        sh = get_screenshotter(page)

        # sidebar 站內信入口（與 i18n/sidebar_locale 同 selector pattern）
        inbox_sidebar = page.locator("div.cursor-pointer", has_text="站內信").first
        inbox_sidebar.scroll_into_view_if_needed()
        if sh: sh.capture(inbox_sidebar, "click_sidebar站內信")
        inbox_sidebar.dispatch_event("click")
        page.wait_for_timeout(1000)

        signal = _panel_open_signal(page)
        expect(signal).to_be_visible(timeout=5000)
        if sh: sh.full_page("verify_站內信面板開啟")

    def test_inbox_tabs_visible(self, class_logged_in_page: Page, go_home):
        """RD-MEMBER-004：個人資訊面板內，站內信區塊有「全部/已讀/未讀」tabs"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        home = HomePage(page)

        home.open_user_dropdown()
        page.wait_for_timeout(800)

        # 點面板內「站內信」按鈕切換到收件匣 view
        # 用 dialog-mask scope 鎖定 panel 內按鈕（非 sidebar 的）
        panel_inbox_btn = page.locator(
            "div.dialog-mask button.group", has_text="站內信"
        ).first
        if panel_inbox_btn.count() > 0:
            panel_inbox_btn.scroll_into_view_if_needed()
            if sh: sh.capture(panel_inbox_btn, "click_面板內站內信")
            panel_inbox_btn.dispatch_event("click")
            page.wait_for_timeout(800)

        # 驗證 3 個 tabs 顯示
        for tab_name in ["全部", "已讀", "未讀"]:
            tab = page.locator("div.dialog-mask button", has_text=tab_name).first
            expect(tab).to_be_visible(timeout=5000)
            if sh: sh.capture(tab, f"verify_收件匣tab_{tab_name}")
