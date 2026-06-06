"""
LU 首頁公告彈窗 功能測試（Dlgbet）
LU-TC-F01 ~ LU-TC-F03

dev-lu 公告用 Nuxt `.dialog-mask` + `.dialog-container.w-full.max-w-[840px]`，
關閉鍵 `.close-wrap`（與 LG 同機制）。

probe 2026-06-06 真相：
- **LU 公告出現在 fresh 載入後約 10 秒**（非 LG 的登入後 popup；也非進站立即出現）
  → 用 `page` fixture（未登入）即可觸發，但 mount 等待需放寬至 20s。
- close-wrap dispatch_event 後整個 `.dialog-mask` 從 DOM 移除（count→0）→ 可用
  `to_have_count(0)` 驗 dismiss。
- 本次 probe 未見圖片廣告層（button.popup-close-btn），僅文字公告；圖片廣告為條件性，
  故本檔只驗文字公告（dismiss_any_popups 仍保留雙層處理）。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter

ANNOUNCE_CONTAINER = ".dialog-container.w-full.max-w-\\[840px\\]"
ANNOUNCE_CLOSE = ".dialog-container.max-w-\\[840px\\] .close-wrap"


@pytest.mark.p1
@pytest.mark.lu
class TestAnnouncementPopup:
    """LU-TC-F01 ~ LU-TC-F03：首頁進站公告行為"""

    def test_popup_mounts_on_home(self, page: Page, site_config):
        """LU-TC-F01：進首頁後公告彈窗 mount 在 DOM（約 10s 後出現，timeout 放寬）"""
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        expect(page.locator(".dialog-mask")).to_have_count(1, timeout=20000)
        expect(page.locator(ANNOUNCE_CONTAINER)).to_have_count(1, timeout=5000)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_公告彈窗_mounted")

    def test_popup_close_dismisses(self, page: Page, site_config):
        """LU-TC-F02：點關閉鍵後公告 mask 從 DOM 移除（count→0）"""
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
        """LU-TC-F03：勾選「今日不再顯示」+ 關閉後，重新進首頁不再出現彈窗"""
        pass
