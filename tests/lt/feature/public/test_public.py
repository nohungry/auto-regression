"""
公開頁延伸功能測試（WAP 版，2026-04-21 rewrite）
WIN-PUB-004~006, 010~011

WAP 改版後的差異（見 memory: project_lt_site_redesign.md）：
- 客服入口：右下浮動 `a#drag_1_container > img[alt="CS"]`，指向 `lin.ee/...`
- 版權 footer：**已移除**（WIN-PUB-006 skip）
- 語系切換 icon：未登入首頁無此入口，改位至登入頁 `span.lang-text`（WIN-PUB-005 skip，i18n PR 再補）
- 未登入首頁無「熱門」分類，改為 `.cat-btn` 五類；先去逛逛後驗 `.cat-btn:has-text("遊戲大廳")`
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.lt.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.lt
class TestPublicFeatures:
    """WIN-PUB-004~006, 010~011：公開頁延伸功能"""

    @pytest.mark.skip(
        reason="WAP iPhone 13 UA 下 img[alt='CS'] 浮動未 mount（CDP desktop UA 下可見）；"
               "bottom tabbar 亦無客服 tab。待確認 WAP mobile 版客服入口實際位置後再補。"
    )
    def test_customer_service_visible(self, page: Page, site_config):
        """WIN-PUB-004：客服入口顯示（待 mobile 版客服入口位置確認）"""

    @pytest.mark.skip(reason="WAP 版未登入首頁已無語系 icon；語系切換改為登入頁 span.lang-text，i18n PR 一併驗證")
    def test_language_icon_visible(self, page: Page, site_config):
        """WIN-PUB-005：語系切換 icon 存在（WAP 不適用）"""

    @pytest.mark.skip(reason="WAP 版首頁已移除版權 footer；DOM 已無 Copyright 文案節點")
    def test_copyright_visible(self, page: Page, site_config):
        """WIN-PUB-006：版權資訊顯示（WAP 不適用）"""

    def test_customer_service_link_is_linee(self, page: Page, site_config):
        """WIN-PUB-010：客服浮動按鈕連結指向 lin.ee"""
        login = LoginPage(page, site_config.url)
        login.goto()
        link = page.locator('a#drag_1_container').first
        expect(link).to_have_attribute("href", re.compile(r"lin\.ee"))
        sh = get_screenshotter(page)
        if sh: sh.capture(link, "verify_客服連結lin.ee")

    def test_browse_without_login_returns_home(self, page: Page, site_config):
        """WIN-PUB-011：登入頁「先去逛逛」可回首頁（驗首頁 .cat-btn 出現）"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)

        browse_btn = page.locator('button.btn-browse').first
        browse_btn.scroll_into_view_if_needed()
        if sh: sh.capture(browse_btn, "click_先去逛逛")
        browse_btn.click()

        expect(page).to_have_url(
            re.compile(r"^" + re.escape(site_config.url.rstrip("/")) + r"/?$"),
            timeout=8000,
        )
        # WAP 首頁以 .cat-btn 「遊戲大廳」為錨點（locale 敏感但與 P0 smoke 一致）
        expect(page.locator('.cat-btn', has_text="遊戲大廳").first).to_be_visible()
        if sh: sh.full_page("verify_回到首頁")
