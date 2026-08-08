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
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lt")


@pytest.mark.p1
@pytest.mark.lt
class TestPublicFeatures:
    """WIN-PUB-004~006, 010~011：公開頁延伸功能"""

    @pytest.mark.skip(reason="[OBSOLETE] 客服入口已由 WIN-PUB-010 test_customer_service_link_exists（active）涵蓋（驗 a.fixed-telegram href 指向 IM 平台）。本 WAP 時代的 img[alt='CS'] 浮動已不存在，永久不適用。")
    def test_customer_service_visible(self, page: Page, site_config):
        """WIN-PUB-004：[OBSOLETE] 客服入口顯示 — 改由 WIN-PUB-010 涵蓋"""

    @pytest.mark.skip(reason="[OBSOLETE] desktop 版未登入首頁無語系切換 icon（probe 2026-06-27 確認）；語系切換移至登入頁頂部 locale dropdown。首頁語系 icon 永久不適用。")
    def test_language_icon_visible(self, page: Page, site_config):
        """WIN-PUB-005：[OBSOLETE] 首頁語系 icon — desktop 已移除（移至登入頁）"""

    @pytest.mark.skip(reason="[OBSOLETE] desktop 版首頁已移除版權 footer（probe 2026-06-27 確認 DOM 無 Copyright/版權 節點）。永久不適用。")
    def test_copyright_visible(self, page: Page, site_config):
        """WIN-PUB-006：[OBSOLETE] 首頁版權 footer — desktop 已移除"""

    def test_customer_service_link_exists(self, page: Page, site_config):
        """WIN-PUB-010：客服浮動按鈕存在且 href 指向支援的 IM 平台。

        2026-05-18 換版：舊 `a#drag_1_container`（指向 lin.ee）已換為 `a.fixed-telegram`，
        href 改為其他 IM 平台。本測試改為驗「客服浮動連結存在且為已知 IM 平台」，
        接受 lin.ee（LINE）/ t.me（Telegram）/ wa.me（WhatsApp）任一即可。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        link = page.locator('a.fixed-telegram, a.fixed-icon').first
        sh = get_screenshotter(page)
        if sh: sh.capture(link, "verify_客服浮動連結存在")
        expect(link).to_have_attribute("href", re.compile(r"(line\.me|lin\.ee|t\.me|wa\.me|telegram)"))

    def test_browse_without_login_returns_home(self, page: Page, site_config):
        """WIN-PUB-011：登入頁「先去逛逛」可回首頁（驗首頁未登入 CTA 出現）

        2026-05-18 換版：button.btn-browse → button.base-btn.type2；首頁未登入錨點
        改用 navbar 「登入」CTA（div.login-btn-with-text，未登入時才顯示）。
        """
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)

        login.browse_btn.scroll_into_view_if_needed()
        if sh: sh.capture(login.browse_btn, "click_先去逛逛")
        login.browse_btn.dispatch_event("click")

        if sh: sh.full_page("verify_回到首頁")
        expect(page).to_have_url(
            re.compile(r"^" + re.escape(site_config.url.rstrip("/")) + r"/?$"),
            timeout=8000,
        )
        # 未登入首頁錨點：navbar 「登入」CTA（locale-agnostic class）
        expect(page.locator('div.login-btn-with-text').first).to_be_visible(timeout=5000)
