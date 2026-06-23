"""
RF 首頁公告彈窗 功能測試（金爺娛樂城）
RF-TC-F01

probe 結果（dev-rf，2026-06-17）：
- rf 站不存在進站公告彈窗機制：
  - 未登入首頁：base-modal/dialog-mask/popup-announcement-mask count 均為 0
  - 登入後首頁：同上，count = 0
  - 登入後重新 goto 首頁並等 15s：仍然 count = 0
  - 探查的彈窗 class 包括：
      .base-modal__container（RF 登入流程用的確認彈窗，非進站公告）
      .dialog-mask（LG/LU 的公告機制，RF 無此 class）
      .popup-announcement-mask（RC 的公告機制，RF 無此 class）
- RF 的 base-modal 只在登入流程（用戶協議/登入成功）出現，非進站公告

設計說明：
- 本檔保留一個「首頁無阻擋性 modal」的 smoke test（RF-TC-F01），
  驗證進入首頁後不存在阻擋點擊的公告彈窗，確保使用者進入首頁時無阻礙。
- 此設計有別於 RC/RE（有進站公告）；比照 where applicable 原則，
  不因 rf 無此功能而硬寫假斷言或空殼測試。
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.rf
class TestAnnouncementPopup:
    """RF-TC-F01：首頁無阻擋性進站公告彈窗

    斷言策略：
    - rf 無進站公告彈窗（probe 實機確認）
    - 驗證常見公告機制的 selector 數量為 0（確保不存在）
    - 驗證主導覽列 nav.menu_nav 可見（確認首頁主內容未被遮蓋）
    - 使用未登入的 page fixture（function-scoped），與登入狀態無關
    """

    def test_no_blocking_popup_on_home(self, page: Page, site_config):
        """RF-TC-F01：進入首頁後不存在阻擋性進站公告彈窗，主導覽列可見

        斷言策略：
        - .base-modal__container count = 0（RF 的 base-modal 只在登入流程出現）
        - .dialog-mask count = 0（LG/LU 的公告機制，RF 無此機制）
        - .popup-announcement-mask count = 0（RC 的公告機制，RF 無此機制）
        - nav.menu_nav 可見（主導覽未被遮蓋）
        備注：驗證「不存在」彈窗後截圖，label 含 _count0 表示非空/0 狀態
        """
        sh = get_screenshotter(page)

        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)

        # 等待 Nuxt hydration 完成（a.btn-login 可見才代表首頁渲染完畢）
        login_entry = page.locator("a.btn-login")
        expect(login_entry).to_be_visible(timeout=15000)

        # 等待 10s 給任何延遲出現的彈窗充裕時間
        page.wait_for_timeout(10000)

        # 截圖後再 assert（先截圖讓失敗時也有證據）
        if sh:
            sh.full_page("verify_首頁進站公告彈窗探查_10s後")

        # 驗證各種已知公告彈窗機制均不存在
        expect(page.locator(".base-modal__container")).to_have_count(0, timeout=3000)
        expect(page.locator(".dialog-mask")).to_have_count(0, timeout=3000)
        expect(page.locator(".popup-announcement-mask")).to_have_count(0, timeout=3000)

        # 主導覽列可見（確認首頁主內容未被任何 overlay 遮蓋）
        nav = page.locator("nav.menu_nav")
        nav.scroll_into_view_if_needed()
        if sh:
            sh.capture(nav, "verify_主導覽列可見_無彈窗遮蓋")
        expect(nav).to_be_visible(timeout=5000)
