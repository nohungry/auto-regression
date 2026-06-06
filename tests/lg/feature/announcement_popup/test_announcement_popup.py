"""
LG 首頁公告彈窗 功能測試（大撈家娛樂城）
LG-TC-F01 ~ LG-TC-F03

dev-lg 公告用 Nuxt `.dialog-mask` + `.dialog-container.w-full.max-w-[840px]` 系統，
關閉鍵為 `.close-wrap`（div，非 button）。

probe 2026-06-06 真相（重要）：
- **公告是「登入後」popup**：未登入首頁 `.dialog-mask` count = 0；登入後首頁才出現
  （opacity:1、pointer-events:auto、會擋點擊），且每次 home reload 重現。
  → 故本檔用 `class_logged_in_page` 登入態驗證，並在每個 test 內自行 goto 首頁觸發公告。
- close-wrap dispatch_event 後**整個 .dialog-mask 從 DOM 移除（count→0）**，可乾淨用
  `to_have_count(0)` 驗 dismiss（不同於 backgrounded fade 卡住的情境）。
- close-wrap 剛出現 boundingRect 為 0 → 必須 dispatch_event 點擊。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter

ANNOUNCE_CONTAINER = ".dialog-container.w-full.max-w-\\[840px\\]"
ANNOUNCE_CLOSE = ".dialog-container.max-w-\\[840px\\] .close-wrap"


@pytest.mark.p1
@pytest.mark.lg
class TestAnnouncementPopup:
    """LG-TC-F01 ~ LG-TC-F03：登入後首頁進站公告行為"""

    def test_popup_mounts_on_home(self, class_logged_in_page: Page, site_config):
        """LG-TC-F01：登入後進首頁，公告彈窗 mount 在 DOM"""
        page = class_logged_in_page
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)

        expect(page.locator(".dialog-mask")).to_have_count(1, timeout=20000)
        expect(page.locator(ANNOUNCE_CONTAINER)).to_have_count(1, timeout=5000)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_公告彈窗_mounted")

    def test_popup_close_dismisses(self, class_logged_in_page: Page, site_config):
        """LG-TC-F02：點關閉鍵後公告 mask 從 DOM 移除（count→0）"""
        page = class_logged_in_page
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)

        mask = page.locator(".dialog-mask")
        expect(mask).to_have_count(1, timeout=20000)

        close_btn = page.locator(ANNOUNCE_CLOSE)
        expect(close_btn).to_have_count(1, timeout=3000)

        sh = get_screenshotter(page)
        if sh: sh.capture(close_btn, "click_關閉鍵")
        # close-wrap boundingRect 為 0（進場動畫）→ dispatch_event 繞過 actionability
        close_btn.dispatch_event("click")

        expect(mask).to_have_count(0, timeout=8000)
        if sh: sh.full_page("verify_關閉後公告移除")

    @pytest.mark.skip(reason="「今日不再顯示」cookie/localStorage 機制待產品確認；點選會影響後續測試")
    def test_popup_dont_show_today(self, class_logged_in_page: Page, site_config):
        """LG-TC-F03：勾選「今日不再顯示」+ 關閉後，重新進首頁不再出現彈窗"""
        pass
