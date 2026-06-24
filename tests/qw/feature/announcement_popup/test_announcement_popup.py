"""
QW 首頁公告彈窗功能測試（LM來財娛樂城）
QW-TC-F01 ~ QW-TC-F03

probe 2026-06-24 實際 DOM 結構：
- 公告彈窗：.popup-mask（全屏 mask）> .popup-frame
  - .popup-close（div，非 button）：含 img[alt="Exit"]
  - .popup-header：顯示「最新公告」
  - .popup-body > .announcement-scroll：公告內容
  - .not-show-row：含 input[type=checkbox] + label「今日不再顯示」
- 彈窗在首頁未登入也會出現（probe 實測：domcontentloaded 後約 5~12s 渲染）
- .popup-mask 的 fade-enter-active → fade-enter-to → 無 class（移除）
- 關閉後 .popup-mask 從 DOM 完整移除（count → 0）

注意：使用 `page` fixture（每 test 獨立 context），避免 class_logged_in_page 的
      go_home 已 dismiss_any_popups 汙染公告彈窗驗證測試。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


POPUP_MASK = ".popup-mask"
POPUP_CLOSE = ".popup-close"
POPUP_FRAME = ".popup-frame"
NOT_SHOW_ROW = ".not-show-row"


@pytest.mark.p1
@pytest.mark.qw
class TestAnnouncementPopup:
    """QW-TC-F01 ~ QW-TC-F03：首頁進站公告行為"""

    def test_popup_mounts_on_home(self, page: Page, site_config):
        """QW-TC-F01：進首頁後公告彈窗 mount 在 DOM（timeout 放寬 15s 等非同步渲染）

        斷言策略：
        - .popup-mask 在 DOM 中 count=1（未必可見 visible，因 fade 動畫可能先 visible 再完成）
        - .popup-frame 存在（確認是公告框而非其他 modal）
        注意：popup-mask 的 visible 時機在 domcontentloaded 後約 5~12s，使用 wait_for count=1。
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        sh = get_screenshotter(page)

        # 等 popup mask 出現（count=1 即可，不強求 visible 以避免動畫 race）
        expect(page.locator(POPUP_MASK)).to_have_count(1, timeout=15000)
        if sh: sh.full_page("verify_popup_mask_mounted")

        expect(page.locator(POPUP_FRAME)).to_have_count(1, timeout=3000)
        if sh: sh.capture(page.locator(POPUP_FRAME), "verify_popup_frame_present")

    def test_popup_close_dismisses(self, page: Page, site_config):
        """QW-TC-F02：點關閉鍵後公告 mask 從 DOM 移除（count→0）

        QW .popup-close 為 div（非 button），dispatch_event 觸發 DOM click。
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        sh = get_screenshotter(page)

        # 等 mask 出現
        mask = page.locator(POPUP_MASK)
        expect(mask).to_have_count(1, timeout=15000)

        # 等關閉 div 可見後截圖再觸發
        close_btn = page.locator(POPUP_CLOSE)
        expect(close_btn).to_have_count(1, timeout=3000)

        close_btn.scroll_into_view_if_needed()
        if sh: sh.capture(close_btn, "click_關閉鍵")
        close_btn.dispatch_event("click")

        # 關閉後 mask 應從 DOM 移除（count→0）
        if sh: sh.full_page("verify_關閉後頁面")
        expect(mask).to_have_count(0, timeout=8000)

    def test_popup_not_show_today_checkbox_present(self, page: Page, site_config):
        """QW-TC-F03：公告彈窗含「今日不再顯示」checkbox

        斷言策略：
        - .not-show-row 容器存在（probe 確認 class 為 not-show-row）
        - 容器內有 input[type=checkbox]（供用戶點選）
        僅驗 UI 存在性，不實際勾選（勾選會影響後續 session 的彈窗顯示行為）。
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        sh = get_screenshotter(page)

        # 等 popup 出現
        expect(page.locator(POPUP_MASK)).to_have_count(1, timeout=15000)

        # 驗「今日不再顯示」row 存在
        not_show_row = page.locator(NOT_SHOW_ROW)
        if sh: sh.full_page("verify_popup_內容")
        expect(not_show_row).to_have_count(1, timeout=5000)

        # 驗 checkbox 存在
        checkbox = not_show_row.locator("input[type='checkbox']")
        if sh: sh.capture(not_show_row, "verify_not_show_today_row")
        expect(checkbox).to_have_count(1, timeout=3000)
