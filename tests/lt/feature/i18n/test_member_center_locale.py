"""
多語系文案驗證 — 個人中心 panel + 底部維護時間 tab（desktop 版，2026-05-18 rewrite）
WIN-I18N-MC-001~005

2026-05-18 換版後：
- 個人中心改為 SPA inline overlay panel（URL 不變），原 /member-center 路由不存在
- 「維護時間」按鈕從 panel 內搬到**底部 footer tab**（`.footer-bg .content` 含「維護」）
- 「投注紀錄」「會員訊息」section 改為 panel 左側 `.sidebar-item` 結構，
  其 i18n 對應字尚未重新 probe，暫不在本檔驗證（留 follow-up）

本檔目前只驗兩個**已確認位置 + 已知 5 語系翻譯**的元素：
- 登出按鈕（panel 內 `button.cancel-btn`）
- 底部維護時間 tab（`.footer-bg .content` 含「維護」）

WAP 時期同檔驗 4 元素，現縮小到 2 元素；待 sidebar items 5 語系翻譯重新 probe 後再擴充。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.lt.home_page import HomePage
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter


# (case_id, locale, maintenance, logout)
# maintenance 為 footer tab 文字（可能是「維護時間」或「維護」，用 to_contain_text 寬鬆比對避免漂移）
_MEMBER_CENTER_LOCALE_CHECKS = [
    ("WIN-I18N-MC-001", "tw", "維護", "登出"),
    ("WIN-I18N-MC-002", "cn", "维护", "登出"),
    ("WIN-I18N-MC-003", "en", "Maintenance", "Logout"),
    ("WIN-I18N-MC-004", "th", "ปิดปรับปรุง", "ออกจากระบบ"),
    ("WIN-I18N-MC-005", "vn", "Bảo trì", "Đăng xuất"),
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

        # 1) 驗 footer 維護時間 tab（locale-agnostic：用 .footer-bg .content 結構定位 + 文字比對）
        # 換版後 footer 各 tab 順序固定，"維護" 通常為第一個 .content
        maint_tab = page.locator(".footer-bg .content").nth(0)
        maint_tab.scroll_into_view_if_needed()
        actual_maint = (maint_tab.inner_text() or "").strip()
        if sh: sh.capture(maint_tab, f"verify_{locale}_footer維護tab_{actual_maint[:15]}")
        assert maint_text in actual_maint, \
            f"{locale} footer 維護 tab 文案應含 '{maint_text}'，實際：{actual_maint}"

        # 2) 開 panel 驗登出按鈕文案
        HomePage(page).open_member_center()
        if sh: sh.full_page(f"verify_{locale}_member_panel_整體")

        logout_btn = page.locator("button.cancel-btn").filter(has_text=logout_text).first
        logout_btn.scroll_into_view_if_needed()
        actual_logout = (logout_btn.inner_text() or "").strip()
        if sh: sh.capture(logout_btn, f"verify_{locale}_登出_{actual_logout[:15]}")
        expect(logout_btn).to_contain_text(logout_text)
