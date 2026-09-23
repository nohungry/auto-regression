"""
會員功能測試 — LT desktop responsive 版（2026-05-18 rewrite）
WIN-MEMBER-001~002

2026-09-13 第三次換版（RC 模板化）後：
- 個人中心＝右側側欄 `.sidebar-item.user` 開的 `.dialog-mask` / `.dialog-container` 彈窗
  （HomePage.open_member_center() 已封裝；URL 維持 /）
- 彈窗內結構：帳號（disabled input，value=帳號）/ 暱稱 / 密碼 / 餘額封頂 / 真人限紅，
  底部登出鈕 `button.dark-red-btn`；**無 balance 顯示**（信用額度在 navbar，由 test_wallet 覆蓋）
- 側欄 7 項：`.sidebar-item.user / .game-details / .game-explosive / .mail / .announce /
  .ranking / .maintain`（容器寬 0，必須 dispatch_event）

本檔驗證 panel 核心可見元素：
- WIN-MEMBER-001：panel 開啟後核心結構（panel 容器 / 帳號資訊 / 登出按鈕 / sidebar items 可見）
- WIN-MEMBER-002：底部 footer 維護時間 tab 可點擊，開啟 dialog overlay
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lt")


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

        # 1) panel 容器（整個 dialog 幾乎滿版，紅框無鑑別度 → 整頁截圖）
        expect(home.member_panel).to_be_visible(timeout=5000)
        if sh: sh.full_page("verify_panel_容器")

        # 2) 帳號欄位（彈窗第一個 disabled input，value 為登入帳號；只驗非空不寫死值）
        account_input = home.member_account_input
        account_input.scroll_into_view_if_needed()
        account_value = (account_input.input_value() or "").strip()
        if sh: sh.capture(account_input, f"verify_帳號欄位非空_{account_value}")
        assert account_value != "", "個人資訊彈窗帳號欄位不應為空"

        # 3) 彈窗內登出按鈕
        home.member_panel_logout_btn.scroll_into_view_if_needed()
        if sh: sh.capture(home.member_panel_logout_btn, "verify_彈窗登出按鈕")
        expect(home.member_panel_logout_btn).to_be_visible()

        # 4) sidebar item（左側 slide-in），至少一個可見即代表 panel 結構完整
        sidebar_item = page.locator(".sidebar-item").first
        sidebar_item.scroll_into_view_if_needed()
        # LT drawer slide-in item 渲染在視窗外（bbox offscreen）→ 整頁截圖呈現實際狀態
        if sh: sh.full_page("verify_sidebar_item_存在")
        expect(sidebar_item).to_be_visible()

    def test_maintenance_time_button_opens_dialog(self, class_logged_in_page: Page, go_home):
        """WIN-MEMBER-002：側欄「固定維護時間」可點擊，開啟維護時間 dialog。

        2026-09-13 換版：底部 footer 整個移除，維護時間改為側欄 `.sidebar-item.maintain`
        （容器寬 0 → 必須 dispatch_event，截圖改用整頁）。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)

        maint_item = page.locator(".sidebar-item.maintain").first
        maint_item.wait_for(state="visible", timeout=10000)
        if sh: sh.full_page("click_側欄固定維護時間")
        maint_item.dispatch_event("click")

        dialog = page.locator(".dialog-mask").first
        dialog.wait_for(state="visible", timeout=10000)
        if sh: sh.full_page("verify_維護時間_dialog_開啟")
        expect(dialog).to_be_visible()
