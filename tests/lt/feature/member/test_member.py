"""
會員功能測試 — LT WAP 版（2026-04-22 rewrite）
WIN-MEMBER-001~002

WAP 改版後：
- 會員入口從 hamburger/drawer 改為底部 tabbar「個人」→ `/member-center`
- /member-center 是獨立頁面（不是 drawer），結構極簡：
  - 餘額顯示（信用額度，LT 為信用板站點，無存款流程）
  - 「維護時間」按鈕（存款功能槽位的佔位，dev 環境顯示為維護時間）
  - 「登出」按鈕
  - 「投注紀錄」/「會員訊息」 section headings（純顯示）
  - 右上角圖示為 `edit.svg`（member info edit 意圖，非關閉按鈕；WAP 無「關閉回首頁」入口）
- 原「個人資料 dialog」、「收件匣 dialog」、「投注紀錄 dialog」等 drawer 時期的 panel 已不存在

本檔驗證 /member-center 核心可見元素與可點擊互動：
- WIN-MEMBER-001：/member-center 核心結構（餘額 / 維護時間 btn / 登出 btn / 投注紀錄 / 會員訊息 可見）
- WIN-MEMBER-002：維護時間按鈕可點擊，開啟 .dialog-mask
"""

import pytest
from playwright.sync_api import Page, expect
from pages.lt.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.member
class TestMemberCenter:
    """WIN-MEMBER-001~003：/member-center 頁面核心驗證"""

    def test_member_center_core_structure(self, class_logged_in_page: Page, go_home):
        """WIN-MEMBER-001：/member-center 核心元素（balance / 維護時間 / 登出 / 投注紀錄 / 會員訊息）皆可見"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_member_center()

        balance = page.locator("p.font-bold.text-amount").first
        maint_btn = page.locator('button.bg-secondary.mb-5').first
        logout_btn = page.locator('button.bg-secondary', has_text="登出").first
        betting_heading = page.locator("p.font-bold", has_text="投注紀錄").first
        msg_heading = page.locator("p.font-bold", has_text="會員訊息").first

        balance.scroll_into_view_if_needed()
        expect(balance).to_be_visible()
        balance_text = (balance.inner_text() or "").strip()
        assert balance_text != "", "member-center 餘額欄位不應為空"
        if sh: sh.capture(balance, f"verify_member_center餘額_{balance_text}")

        maint_btn.scroll_into_view_if_needed()
        expect(maint_btn).to_be_visible()
        if sh: sh.capture(maint_btn, "verify_維護時間按鈕")

        logout_btn.scroll_into_view_if_needed()
        expect(logout_btn).to_be_visible()
        if sh: sh.capture(logout_btn, "verify_登出按鈕")

        betting_heading.scroll_into_view_if_needed()
        expect(betting_heading).to_be_visible()
        if sh: sh.capture(betting_heading, "verify_投注紀錄標題")

        msg_heading.scroll_into_view_if_needed()
        expect(msg_heading).to_be_visible()
        if sh: sh.capture(msg_heading, "verify_會員訊息標題")

        if sh: sh.full_page("verify_member_center_整體")

    def test_maintenance_time_button_opens_dialog(self, class_logged_in_page: Page, go_home):
        """WIN-MEMBER-002：點擊「維護時間」按鈕會彈出 .dialog-mask。

        LT 為信用板站點，無存款流程；此按鈕為存款功能槽位佔位，dev 顯示為「維護時間」。
        只驗「按鈕存在、可點擊開啟 dialog」，不驗 dialog 內容語意。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_member_center()

        maint_btn = page.locator('button.bg-secondary.mb-5').first
        maint_btn.scroll_into_view_if_needed()
        if sh: sh.capture(maint_btn, "click_維護時間")
        maint_btn.click()

        dialog_mask = page.locator('.dialog-mask').first
        expect(dialog_mask).to_be_visible(timeout=5000)
        if sh: sh.full_page("verify_維護時間dialog開啟")

