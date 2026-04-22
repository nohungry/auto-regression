"""
多語系文案驗證 — /member-center 頁面（WAP 版，2026-04-22 rewrite）
WIN-I18N-MC-001~005

WAP 改版後，會員入口從 hamburger/drawer 改為底部 tabbar「個人」→ `/member-center` 頁面。
此檔原名 `test_drawer_locale.py`，已隨產品改版 rename 為 `test_member_center_locale.py`。

WAP 多語系實測（2026-04-22 probe）：
- `/member-center` 的 **按鈕與 section 標題** 都有正確 5 語系翻譯：
  - 「維護時間」按鈕（`button.bg-secondary.mb-5`）
  - 「登出」按鈕（`button.bg-secondary` 非 mb-5）
  - 「投注紀錄」heading
  - 「會員訊息」heading
- 但底部 tabbar（維護/公告/排行榜/個人）在所有語系下仍固定為繁中（產品端未套 i18n，見 test_home_locale.py）。

本檔驗證 /member-center 四項核心文案在 5 語系下正確翻譯。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.lt.home_page import HomePage
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter


# (case_id, locale, maintenance, logout, betting_record, member_messages)
_MEMBER_CENTER_LOCALE_CHECKS = [
    ("WIN-I18N-MC-001", "tw", "維護時間",             "登出",          "投注紀錄",            "會員訊息"),
    ("WIN-I18N-MC-002", "cn", "维护时间",             "登出",          "投注记录",            "会员讯息"),
    ("WIN-I18N-MC-003", "en", "Maintenance Time",    "Logout",       "Betting Record",     "Member Messages"),
    ("WIN-I18N-MC-004", "th", "ช่วงเวลาบำรุงรักษา",    "ออกจากระบบ",     "ประวัติการเดิมพัน",   "ข้อมูลสมาชิก"),
    ("WIN-I18N-MC-005", "vn", "Bảo trì",             "Đăng xuất",     "Lịch sử cược",      "Tài khoản"),
]


@pytest.mark.p2
@pytest.mark.lt
@pytest.mark.i18n
class TestI18NMemberCenter:
    """WIN-I18N-MC-001~005：各語系 /member-center 文案驗證"""

    @pytest.mark.parametrize("case_id,locale,maint_text,logout_text,betting_text,msg_text",
                             _MEMBER_CENTER_LOCALE_CHECKS,
                             ids=[c[0] for c in _MEMBER_CENTER_LOCALE_CHECKS])
    def test_member_center_locale_text(self, logged_in_page: Page, site_config, case_id, locale,
                                       maint_text, logout_text, betting_text, msg_text):
        """各語系 /member-center 四項核心文案正確翻譯"""
        page = logged_in_page
        sh = get_screenshotter(page)

        # 切 locale 並回首頁重新渲染
        set_locale(page, site_config.url, locale)
        page.goto(site_config.url, wait_until="networkidle")

        # 進 /member-center（底部個人 tab 在所有語系下固定繁中「個人」，has_text="個人" 皆可命中）
        HomePage(page).open_member_center()

        maint_btn = page.locator('button.bg-secondary.mb-5').first
        logout_btn = page.locator('button.bg-secondary').nth(1)
        betting_heading = page.locator("p.font-bold", has_text=betting_text).first
        msg_heading = page.locator("p.font-bold", has_text=msg_text).first

        maint_btn.scroll_into_view_if_needed()
        expect(maint_btn).to_have_text(maint_text)
        if sh: sh.capture(maint_btn, f"verify_{locale}_維護時間_{maint_text[:15]}")

        logout_btn.scroll_into_view_if_needed()
        expect(logout_btn).to_have_text(logout_text)
        if sh: sh.capture(logout_btn, f"verify_{locale}_登出_{logout_text[:15]}")

        betting_heading.scroll_into_view_if_needed()
        expect(betting_heading).to_have_text(betting_text)
        if sh: sh.capture(betting_heading, f"verify_{locale}_投注紀錄_{betting_text[:15]}")

        msg_heading.scroll_into_view_if_needed()
        expect(msg_heading).to_have_text(msg_text)
        if sh: sh.capture(msg_heading, f"verify_{locale}_會員訊息_{msg_text[:15]}")

        if sh: sh.full_page(f"verify_{locale}_member_center_整體")
