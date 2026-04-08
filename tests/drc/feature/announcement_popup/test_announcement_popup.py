"""
首頁公告大圖輪播彈窗 功能測試
TC-F01 ~ TC-F04
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
class TestAnnouncementPopup:
    """
    TC-F01 ~ TC-F04：首頁公告大圖輪播彈窗行為

    使用 page fixture（function-scoped，每個測試獨立 context）。
    理由：「今天不再顯示」功能會將狀態寫入 cookie/localStorage，
    若共用 session 則後續測試可能看不到 popup，造成污染。
    進入首頁不需登入即可觸發彈窗，無需走完整登入流程。
    """

    def test_popup_appears_on_home(self, page: Page, site_config):
        """TC-F01：進入首頁後公告輪播彈窗自動出現"""
        page.goto(site_config.url)
        page.wait_for_load_state("networkidle")
        mask = page.locator(".popup-announcement-mask")
        expect(mask).to_be_visible(timeout=5000)
        sh = get_screenshotter(page)
        if sh: sh.capture(mask, "verify_公告彈窗出現")

    def test_popup_close_btn_advances_slide(self, page: Page, site_config):
        """TC-F02：點擊 ✕ 後輪播推進下一張（彈窗仍存在，未直接關閉）"""
        page.goto(site_config.url)
        page.wait_for_load_state("networkidle")
        mask = page.locator(".popup-announcement-mask")
        expect(mask).to_be_visible(timeout=5000)

        close_btn = page.locator("button.close-circle-btn")
        expect(close_btn).to_be_visible(timeout=3000)
        close_btn.scroll_into_view_if_needed()
        sh = get_screenshotter(page)
        if sh: sh.capture(close_btn, "click_關閉按鈕_第一張")
        close_btn.click()

        # 點擊後 popup 仍在，代表推進至下一張而非直接關閉
        # 若只有一張投影片則此測試 fail — 屬預期行為，反映測試環境 popup 為單張
        expect(mask).to_be_visible(timeout=3000)
        if sh: sh.capture(mask, "verify_輪播推進後彈窗仍存在")

    def test_popup_closes_after_all_slides(self, page: Page, site_config):
        """TC-F03：持續點擊 ✕ 後公告彈窗最終完全消失"""
        page.goto(site_config.url)
        page.wait_for_load_state("networkidle")
        mask = page.locator(".popup-announcement-mask")
        expect(mask).to_be_visible(timeout=5000)

        sh = get_screenshotter(page)
        close_btn = page.locator("button.close-circle-btn")
        for i in range(30):
            try:
                close_btn.wait_for(state="visible", timeout=1000)
                # close-circle-btn 在全螢幕 overlay 內，必在 viewport，不需 scroll
                # 最後一張關閉後元素被 DOM 移除，若呼叫 scroll_into_view_if_needed() 會 detach error
                if sh: sh.capture(close_btn, f"click_關閉按鈕_第{i + 1}次")
                close_btn.click()
            except PlaywrightTimeoutError:
                break

        expect(mask).not_to_be_visible(timeout=3000)
        if sh: sh.full_page("verify_公告彈窗已完全關閉")

    @pytest.mark.skip(reason="「今天不再顯示」行為待確認，暫不自動化")
    def test_popup_dont_show_today(self, page: Page, site_config):
        """TC-F04：勾選「今天不再顯示」後，重新進入首頁不再出現彈窗（待確認行為）"""
        pass
