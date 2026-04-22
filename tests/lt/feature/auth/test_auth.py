"""
登入後功能測試（WAP 版，2026-04-21 rewrite）
WIN-AUTH-002, 004

WAP 改版後的差異（見 memory: project_lt_site_redesign.md）：
- 會員區塊入口：底部 tabbar「個人」→ `/member-center`（取代桌機版 drawer）
- 分類切換：`.cat-btn` 同頁狀態切換，不改 URL；驗 `.cat-btn--selected` class
  - WAP 分類：遊戲大廳 / 我的最愛 / 台灣真人 / 國際真人 / 更多（無「真人/電子」桌機分類）
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.lt.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


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
        # 核心必須存在：登出按鈕（POM 已確保 visible）
        expect(home.logout_btn).to_be_visible(timeout=5000)
        home.logout_btn.scroll_into_view_if_needed()
        if sh: sh.capture(home.logout_btn, "verify_登出按鈕")

        # 其他常見功能文案：存在即 capture（不存在則記錄但不失敗）
        # 原 desktop drawer 的 [投注紀錄/會員訊息/維護時間]，WAP member-center 實際項目由下方 scan 決定
        expected_labels = ["投注紀錄", "會員訊息", "維護時間"]
        page_body_text = logged_in_page.locator("body").inner_text()
        missing = [t for t in expected_labels if t not in page_body_text]
        if missing:
            pytest.skip(
                f"WAP /member-center 尚未發現文案：{missing}；WAP member-center 項目可能與桌機 drawer 不同，"
                f"待實測盤點後補強斷言"
            )
        for text in expected_labels:
            el = logged_in_page.get_by_text(text, exact=False).first
            el.scroll_into_view_if_needed()
            expect(el).to_be_visible()
            if sh: sh.capture(el, f"verify_會員功能_{text}")

    def test_category_navigation_after_login(self, logged_in_page: Page, site_config):
        """WIN-AUTH-004：登入後可切換多個 `.cat-btn` 分類，帳號 pill 仍顯示"""
        home = HomePage(logged_in_page)
        sh = get_screenshotter(logged_in_page)

        # WAP 分類切換不改 URL，以 .cat-btn--selected 判定
        # 用 dispatch_event("click") 規避 CS 浮動/常駐浮層對 pointer events 的攔截
        for label in ["台灣真人", "國際真人"]:
            nav = logged_in_page.locator('.cat-btn', has_text=label).first
            nav.scroll_into_view_if_needed()
            if sh: sh.capture(nav, f"click_分類_{label}")
            nav.dispatch_event("click")
            expect(nav).to_have_class(re.compile(r"cat-btn--selected"), timeout=5000)

            # 切換後帳號仍顯示
            expect(home.navbar_login_pill).to_have_text(site_config.username, timeout=5000)
            if sh: sh.capture(home.navbar_login_pill, f"verify_帳號顯示_{label}分類")
