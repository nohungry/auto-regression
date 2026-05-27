"""
RD 首頁公告彈窗 功能測試 (狗狗娛樂城)
RD-TC-F01 ~ RD-TC-F03

dev-rd 公告彈窗用 `.dialog-mask` + `.dialog-container`（Nuxt dialog 系統，
與 RC 的 `.popup-announcement-mask` 結構不同）。彈窗內容包含公告文字 +
「今日不再顯示」勾選 + 「關閉」按鈕。

驗證策略：
- 在 backgrounded CDP 下 Vue `<Transition>` fade-in 不觸發（class 停在
  `fade-enter-from fade-enter-active`、opacity:0），無法用 `to_be_visible()`
  斷言。改用 `to_have_count()` 驗證 DOM mount 狀態，輔以截圖人工檢視。
- 「關閉」按鈕點擊後 dialog 從 DOM 移除（含 fade-out）。

使用 page fixture（function-scoped，每個測試獨立 context），避免 cookie 殘留
影響「今日不再顯示」這類狀態相關測試。進入首頁不需登入即可觸發彈窗。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.rd
class TestAnnouncementPopup:
    """RD-TC-F01 ~ RD-TC-F03：首頁公告彈窗行為"""

    def test_popup_mounts_on_home(self, page: Page, site_config):
        """RD-TC-F01：進入首頁後公告彈窗 mount 在 DOM"""
        page.goto(site_config.url, wait_until="domcontentloaded")
        mask = page.locator(".dialog-mask")
        expect(mask).to_have_count(1, timeout=10000)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_公告彈窗_mounted")

    def test_popup_close_btn_dismisses(self, page: Page, site_config):
        """RD-TC-F02：點「關閉」按鈕後公告彈窗從 DOM 移除"""
        page.goto(site_config.url, wait_until="domcontentloaded")
        mask = page.locator(".dialog-mask")
        expect(mask).to_have_count(1, timeout=10000)

        close_btn = page.locator(".dialog-container button", has_text="關閉")
        expect(close_btn).to_have_count(1, timeout=3000)

        sh = get_screenshotter(page)
        if sh: sh.capture(close_btn, "click_關閉按鈕")
        # dialog-mask 是 fixed overlay，pointer-events 攔截可能存在；
        # 用 dispatch_event 繞過 actionability check（同 home_page.logout pattern）
        close_btn.dispatch_event("click")

        # Vue Transition fade-out 可能需 1~2 秒；放寬 timeout 至 5s
        expect(mask).to_have_count(0, timeout=5000)
        if sh: sh.full_page("verify_關閉後彈窗消失")

    @pytest.mark.skip(reason="「今日不再顯示」行為待產品確認 cookie/localStorage 機制")
    def test_popup_dont_show_today(self, page: Page, site_config):
        """RD-TC-F03：勾選「今日不再顯示」+ 關閉後，重新進入首頁不再出現彈窗"""
        pass
