"""
多語系文案驗證 — 個人中心 panel + 底部維護時間 tab（desktop 版，2026-05-18 rewrite）
WIN-I18N-MC-001~005

2026-09-13 第三次換版（RC 模板化）後：
- 個人中心＝側欄 `.sidebar-item.user` 開的 `.dialog-mask` 彈窗（URL 不變）
- 底部 footer 已整個移除；「固定維護時間」改為側欄 `.sidebar-item.maintain`
- 彈窗登出鈕改為 `.dialog-container button.dark-red-btn`

本檔仍驗兩個元素（側欄維護入口 + 彈窗登出鈕）的 5 語系文案。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lt")


# (case_id, locale, maintenance, logout)
# maintenance 為側欄「固定維護時間」入口文字（2026-09-13 換版後由 footer tab 改為
# .sidebar-item.maintain），用 in / to_contain_text 寬鬆比對避免文案漂移
_MEMBER_CENTER_LOCALE_CHECKS = [
    ("WIN-I18N-MC-001", "tw", "維護", "登出"),
    ("WIN-I18N-MC-002", "cn", "维护", "登出"),
    ("WIN-I18N-MC-003", "en", "Maintenance", "Logout"),
    # th/vn 的維護關鍵字在 2026-09-13 換版後改用新入口「固定維護時間（供應商）」的用詞，
    # 且句中為小寫（vn: "Thời gian bảo trì nhà cung cấp"），故 keyword 取句中實際片段
    ("WIN-I18N-MC-004", "th", "บำรุงรักษา", "ออกจากระบบ"),
    ("WIN-I18N-MC-005", "vn", "bảo trì", "Đăng xuất"),
]


@pytest.mark.p2
@pytest.mark.lt
@pytest.mark.i18n
class TestI18NMemberCenter:
    """WIN-I18N-MC-001~005：各語系 member panel 登出按鈕 + footer 維護 tab 文案"""

    @pytest.mark.parametrize("case_id,locale,maint_text,logout_text",
                             _MEMBER_CENTER_LOCALE_CHECKS,
                             ids=[c[0] for c in _MEMBER_CENTER_LOCALE_CHECKS])
    def test_member_center_locale_text(self, logged_in_page: Page, site_config, case_id, locale,
                                       maint_text, logout_text):
        """各語系 panel 內登出按鈕 + footer 維護 tab 文案正確翻譯"""
        page = logged_in_page
        sh = get_screenshotter(page)

        # 切 locale 並回首頁重新渲染
        set_locale(page, site_config.url, locale)
        page.goto(site_config.url, wait_until="networkidle")

        # 1) 驗側欄「固定維護時間」入口文案（2026-09-13 換版：底部 footer 已移除，
        #    維護時間改為側欄 .sidebar-item.maintain；容器寬 0 故用整頁截圖當證據）
        home = HomePage(page)
        maint_item = page.locator(".sidebar-item.maintain").first
        maint_item.wait_for(state="visible", timeout=10000)
        actual_maint = (maint_item.inner_text() or "").strip()
        if sh: sh.full_page(f"verify_{locale}_側欄維護入口_{actual_maint[:15]}")
        assert maint_text in actual_maint, \
            f"{locale} 側欄維護入口文案應含 '{maint_text}'，實際：{actual_maint}"

        # 2) 開個人資訊彈窗驗登出按鈕文案
        home.open_member_center()
        if sh: sh.full_page(f"verify_{locale}_member_panel_整體")

        logout_btn = home.member_panel_logout_btn
        logout_btn.scroll_into_view_if_needed()
        actual_logout = (logout_btn.inner_text() or "").strip()
        if sh: sh.capture(logout_btn, f"verify_{locale}_登出_{actual_logout[:15]}")
        expect(logout_btn).to_contain_text(logout_text)
