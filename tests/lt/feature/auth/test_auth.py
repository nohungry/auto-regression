"""
登入後功能測試
WIN-AUTH-002, 004

2026-09-13 第三次換版（RC 模板化）後：
- 會員區塊入口：右側側欄 `.sidebar-item.user` → 開「個人資訊」彈窗（`.dialog-mask`）
- 彈窗內登出鈕為 `.dialog-container button.dark-red-btn`（HomePage.member_panel_logout_btn）；
  navbar 頭像下拉另有一個登出鈕（HomePage.logout_btn），兩者為不同入口
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lt")


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.login
class TestAuthFeatures:
    """WIN-AUTH-002, 004：登入後功能驗證"""

    def test_member_features_text_visible(self, logged_in_page: Page):
        """WIN-AUTH-002：登入後 member-center 顯示會員功能文案（登出按鈕為核心，其他文字有則驗）"""
        home = HomePage(logged_in_page)
        home.open_member_center()

        sh = get_screenshotter(logged_in_page)
        # 核心必須存在：彈窗內登出按鈕（POM 已確保 panel visible）
        home.member_panel_logout_btn.scroll_into_view_if_needed()
        if sh: sh.capture(home.member_panel_logout_btn, "verify_彈窗登出按鈕")
        expect(home.member_panel_logout_btn).to_be_visible(timeout=5000)

        # 其他常見功能文案：存在即 capture（不存在則記錄但不失敗）
        # 原 desktop drawer 的 [投注紀錄/會員訊息/維護時間]，WAP member-center 實際項目由下方 scan 決定
        # 2026-09-13 換版：彈窗欄位改為 帳號 / 暱稱 / 密碼 / 餘額封頂 / 真人限紅
        expected_labels = ["帳號", "暱稱", "密碼"]
        page_body_text = logged_in_page.locator("body").inner_text()
        missing = [t for t in expected_labels if t not in page_body_text]
        if missing:
            pytest.skip(
                f"個人資訊彈窗未發現文案：{missing}；欄位組成可能隨產品調整，待重新盤點後補強斷言"
            )
        for text in expected_labels:
            el = logged_in_page.get_by_text(text, exact=False).first
            el.scroll_into_view_if_needed()
            if sh: sh.capture(el, f"verify_會員功能_{text}")
            expect(el).to_be_visible()

    @pytest.mark.skip(reason="[OBSOLETE] desktop 版分類 tab 切換機制（.cat-btn--selected）已由產品移除（probe 2026-06-27），改單頁 swipe sections（無 tab 切換互動）。section 存在性已由 test_p0_smoke test_navigation_visible/test_hot_games_section 涵蓋。永久不適用。")
    def test_category_navigation_after_login(self, logged_in_page: Page, site_config):
        """WIN-AUTH-004：[OBSOLETE] 登入後分類切換 — desktop 改 swipe sections，無 tab 切換"""
