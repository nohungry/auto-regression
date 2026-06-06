"""
KS 首頁公告彈窗 功能測試（Super9娛樂城）
KS-TC-F01 ~ KS-TC-F03

dev-ks 公告用 Nuxt `.dialog-mask` + `.dialog-container.w-full.max-w-[840px]`，
關閉鍵 `.close-wrap`（與 LG/LU 同機制）。

probe 2026-06-06：
- 公告出現在 fresh 載入後約 12 秒（未登入即觸發）→ 用 `page` fixture，mount 等待放寬 20s。
- close-wrap dispatch_event 後整個 `.dialog-mask` 從 DOM 移除（count→0）。
  （smoke 註記的「dev mask transition 卡死」本次未重現；若日後 dismiss 卡住，
  改驗 mask opacity/pointer-events 而非 count。）
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter

ANNOUNCE_CONTAINER = ".dialog-container.w-full.max-w-\\[840px\\]"
ANNOUNCE_CLOSE = ".dialog-container.max-w-\\[840px\\] .close-wrap"


@pytest.mark.p1
@pytest.mark.ks
class TestAnnouncementPopup:
    """KS-TC-F01 ~ KS-TC-F03：首頁進站公告行為"""

    def test_popup_mounts_on_home(self, page: Page, site_config):
        """KS-TC-F01：進首頁後公告彈窗 mount 在 DOM（約 12s 後出現，timeout 放寬）"""
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        expect(page.locator(".dialog-mask")).to_have_count(1, timeout=20000)
        expect(page.locator(ANNOUNCE_CONTAINER)).to_have_count(1, timeout=5000)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_公告彈窗_mounted")

    def test_popup_close_dismisses(self, page: Page, site_config):
        """KS-TC-F02：點關閉鍵後公告 mask 從 DOM 移除（count→0）"""
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        mask = page.locator(".dialog-mask")
        expect(mask).to_have_count(1, timeout=20000)

        close_btn = page.locator(ANNOUNCE_CLOSE)
        expect(close_btn).to_have_count(1, timeout=3000)

        sh = get_screenshotter(page)
        if sh: sh.capture(close_btn, "click_關閉鍵")
        close_btn.dispatch_event("click")

        expect(mask).to_have_count(0, timeout=8000)
        if sh: sh.full_page("verify_關閉後公告移除")

    @pytest.mark.skip(reason="「今日不再顯示」cookie/localStorage 機制待產品確認；點選會影響後續測試")
    def test_popup_dont_show_today(self, page: Page, site_config):
        """KS-TC-F03：勾選「今日不再顯示」+ 關閉後，重新進首頁不再出現彈窗"""
        pass
