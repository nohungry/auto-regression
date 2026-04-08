"""
多語系文案驗證 — 會員 Drawer 選單
WIN-I18N-DRAWER-001~005

注意：不使用 HomePage.open_member_drawer()，因該方法依賴繁中「登出」按鈕等待，
在 en/th/vn 語系下 logout 文案不同會 timeout。
改用 img src（locale-agnostic）確認 drawer 已展開。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter


_DRAWER_LOCALE_CHECKS = [
    # (case_id, locale, betting_text, inbox_text, maint_text)
    ("WIN-I18N-DRAWER-001", "tw", "投注紀錄",            "會員訊息",          "維護時間"),
    ("WIN-I18N-DRAWER-002", "cn", "投注记录",            "会员讯息",          "维护时间"),
    ("WIN-I18N-DRAWER-003", "en", "Betting Record",    "Member Messages", "Maintenance Time"),
    ("WIN-I18N-DRAWER-004", "th", "ประวัติการเดิมพัน",  "ข้อมูลสมาชิก",    "ช่วงเวลาบำรุงรักษา"),
    ("WIN-I18N-DRAWER-005", "vn", "Lịch sử cược",     "Tài khoản",       "Bảo trì"),
]


@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.i18n
class TestI18NMemberDrawer:
    """WIN-I18N-DRAWER-001~005：各語系會員 Drawer 選單文案驗證"""

    @pytest.mark.parametrize("case_id,locale,betting_text,inbox_text,maint_text",
                             _DRAWER_LOCALE_CHECKS,
                             ids=[c[0] for c in _DRAWER_LOCALE_CHECKS])
    def test_drawer_locale_text(self, logged_in_page: Page, site_config, case_id, locale,
                                betting_text, inbox_text, maint_text):
        """各語系 Drawer 選單項目文案正確顯示"""
        page = logged_in_page
        sh = get_screenshotter(page)

        # 切換語系並重載首頁
        set_locale(page, site_config.url, locale)
        page.goto(site_config.url, wait_until="networkidle")

        # 開啟 drawer（使用 img src 等待，locale-agnostic）
        page.locator(".hamburger").first.dispatch_event("click")
        page.locator('img[src*="betting-details"]').wait_for(state="visible", timeout=5000)

        # 驗證選單文案（定位用 img src，text 用 sibling p）
        betting_el = page.locator('img[src*="betting-details"]').locator('..').locator('p')
        inbox_el   = page.locator('img[src*="member-messages"]').locator('..').locator('p')
        maint_el   = page.locator("button[class*='mb-5']").first

        expect(betting_el).to_have_text(betting_text)
        expect(inbox_el).to_have_text(inbox_text)
        expect(maint_el).to_have_text(maint_text)
        if sh: sh.full_page(f"verify_{locale}_drawer文案")
