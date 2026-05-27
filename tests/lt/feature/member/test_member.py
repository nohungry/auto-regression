"""
會員功能測試 — LT desktop responsive 版（2026-05-18 rewrite）
WIN-MEMBER-001~002

2026-05-18 換版後：
- 個人中心**不再是 /member-center 獨立路由**，URL 維持 /；底部「個人」tab 開
  `.dialog-mask-full` overlay panel（HomePage.open_member_center() 已封裝）
- panel 內結構大改：
  - **無 balance 顯示**（信用額度只在 navbar `.coin-wrap-bg span`，由 test_wallet 覆蓋）
  - **無「維護時間」按鈕**（維護時間改為底部 footer 一個 tab `.footer-bg .content` 含「維護」）
  - 帳號資訊區 `.dialog-scrollable div.tip-single` 含「帳號：」「暱稱：」「ID：」
  - sidebar items（左側 slide-in）：`.sidebar-item.user / .game-details / .maintain / .mail`
  - 登出按鈕：`button.cancel-btn` filter has_text "登出"（無確認 dialog）

本檔驗證 panel 核心可見元素：
- WIN-MEMBER-001：panel 開啟後核心結構（panel 容器 / 帳號資訊 / 登出按鈕 / sidebar items 可見）
- WIN-MEMBER-002：底部 footer 維護時間 tab 可點擊，開啟 dialog overlay
"""

import pytest
from playwright.sync_api import Page, expect
from pages.lt.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.member
class TestMemberCenter:
    """WIN-MEMBER-001~002：個人中心 panel + footer 維護時間驗證"""

    def test_member_center_core_structure(self, class_logged_in_page: Page, go_home):
        """WIN-MEMBER-001：個人中心 panel 開啟後，核心元素皆可見
        （panel container / 帳號資訊行 / 登出按鈕 / 至少一個 sidebar item）

        信用額度顯示位置已搬到 navbar，由 test_wallet 覆蓋。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_member_center()

        if sh: sh.full_page("verify_member_center_panel_整體")

        # 1) panel 容器
        expect(home.member_panel).to_be_visible(timeout=5000)
        if sh: sh.capture(home.member_panel, "verify_panel_容器")

        # 2) 帳號資訊行（包含「帳號：」固定 label，所有語系下都有冒號）
        account_row = (
            page.locator(".dialog-scrollable div.tip-single, .dialog-scrollable p.tip-single")
            .filter(has_text="：")
            .first
        )
        account_row.scroll_into_view_if_needed()
        if sh: sh.capture(account_row, "verify_帳號資訊行")
        expect(account_row).to_be_visible()

        # 3) 登出按鈕
        home.logout_btn.scroll_into_view_if_needed()
        if sh: sh.capture(home.logout_btn, "verify_登出按鈕")
        expect(home.logout_btn).to_be_visible()

        # 4) sidebar item（左側 slide-in），至少一個可見即代表 panel 結構完整
        sidebar_item = page.locator(".sidebar-item").first
        sidebar_item.scroll_into_view_if_needed()
        if sh: sh.capture(sidebar_item, "verify_sidebar_item_存在")
        expect(sidebar_item).to_be_visible()

    def test_maintenance_time_button_opens_dialog(self, class_logged_in_page: Page, go_home):
        """WIN-MEMBER-002：底部 footer「維護」tab 可點擊，開啟維護時間 dialog overlay。

        2026-05-18 換版：維護時間從 member-center panel 內按鈕搬到底部 footer 一個 tab。
        Selector：`.footer-bg .content` filter has_text "維護"，需 dispatch_event。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        maint_tab = page.locator(".footer-bg .content").filter(has_text="維護").first
        maint_tab.wait_for(state="visible", timeout=5000)
        if sh: sh.capture(maint_tab, "click_維護時間_footer_tab")
        maint_tab.dispatch_event("click")

        # 觸發後新增一個 .dialog-mask-full（與 member panel 同類但獨立實例）
        dialog = page.locator(".dialog-mask-full").last
        dialog.wait_for(state="visible", timeout=5000)
        if sh: sh.full_page("verify_維護時間_dialog_開啟")
        expect(dialog).to_be_visible()
