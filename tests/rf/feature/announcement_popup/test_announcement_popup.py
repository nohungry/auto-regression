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
from pages.factory import get_login_page_class, get_home_page_class
from utils.screenshot_helper import get_screenshotter

# RF 唯一「進站彈窗」等效物 = 登入流程 base-modal（用戶協議首次 + 登入成功每次）。
# 可見 base-modal 計數：與 pages/rf/login_page.py 相同的 offsetParent heuristic，
# 對 v-if（移出 DOM）與 v-show（display:none）皆準，取代不確定的 to_have_count(0)。
_VISIBLE_MODAL_COUNT_JS = (
    "() => Array.from(document.querySelectorAll('.base-modal__container'))"
    ".filter(e => e.offsetParent !== null).length"
)


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


@pytest.mark.p1
@pytest.mark.rf
class TestLoginModalBehavior:
    """RF-TC-F02 ~ F03：登入流程 base-modal（RF 的「進站彈窗」等效物）行為

    背景：
    - RF 無 RC/RE 式進站公告、亦無 LG/LU/KS 式 .dialog-mask 公告（probe 2026-06-17）。
    - RF 首頁路徑上唯一會出現的 modal 是登入流程的 base-modal（用戶協議首次 + 登入成功每次），
      關閉控制項為 button.btn-gold（非鄰站的 .close-wrap）。
    - 故將鄰站 LG/LU/KS 的「公告結構完整性 / 關閉後不殘留」概念，映射到 RF 結構上成立的
      登入 base-modal，selector 全數取自 pages/rf/login_page.py 與 home_page.py。
    - 使用 page fixture 自行驅動 POM 登入（與本檔既有 F01 同用 page fixture），非 class_logged_in_page，
      因為需在測試內觀察 base-modal 出現→關閉的完整生命週期。
    """

    def test_login_modal_has_close_control(self, page: Page, site_config):
        """RF-TC-F02：登入流程 base-modal 可見時內含關閉(確定)控制項

        對應鄰站 LG/LU/KS test_popup_mounts_on_home（公告 container 可見且內含 .close-wrap 關閉鍵）。
        差異：RF 為登入流程 base-modal（非進站公告），關閉控制項為 button.btn-gold。
        斷言策略：送出登入後 .base-modal__container 可見、且其內 button.btn-gold 可見（可關閉）。
        收尾以 complete_login_modals() 清乾淨，讓 auto_logout_after_test 正常登出。
        """
        LoginPage = get_login_page_class("rf")
        login = LoginPage(page, site_config.url)
        sh = get_screenshotter(page)

        login.goto()
        login.open_login_form()
        login.login(site_config.username, site_config.password)

        container = page.locator(".base-modal__container").first
        expect(container).to_be_visible(timeout=15000)

        confirm_btn = page.locator(".base-modal__container button.btn-gold").first
        confirm_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(confirm_btn, "verify_base_modal關閉控制項可見")
        expect(confirm_btn).to_be_visible(timeout=5000)

        # 收尾：清除登入流程 base-modal
        login.complete_login_modals()

    def test_login_modal_dismiss_no_residual_mask(self, page: Page, site_config):
        """RF-TC-F03：登入流程 base-modal 關閉後不殘留遮罩、首頁可互動

        對應鄰站 LG/LU/KS test_popup_close_dismisses（關閉後 .dialog-mask count→0）。
        差異：RF 關閉的是登入流程 base-modal；以與 POM 相同的 offsetParent heuristic
        判「可見 base-modal 數 = 0」（相容 v-if / v-show），而非鄰站的 to_have_count(0)。
        關閉後另驗首頁可互動：主導覽 nav.menu_nav 與已登入信號 .info_name 可見。
        """
        LoginPage = get_login_page_class("rf")
        HomePage = get_home_page_class("rf")
        login = LoginPage(page, site_config.url)
        home = HomePage(page)
        sh = get_screenshotter(page)

        login.goto()
        login.open_login_form()
        login.login(site_config.username, site_config.password)

        # base-modal 先出現，再關閉
        expect(page.locator(".base-modal__container").first).to_be_visible(timeout=15000)
        login.complete_login_modals()

        if sh:
            sh.full_page("verify_base_modal關閉後_無殘留遮罩")

        # 無殘留可見遮罩（offsetParent heuristic，與 login_page 一致）
        visible_modals = page.evaluate(_VISIBLE_MODAL_COUNT_JS)
        assert visible_modals == 0, (
            f"登入流程 base-modal 關閉後仍有 {visible_modals} 個可見遮罩殘留"
        )

        # 首頁可互動：主導覽可見
        nav = page.locator("nav.menu_nav")
        nav.scroll_into_view_if_needed()
        if sh:
            sh.capture(nav, "verify_首頁可互動_主導覽可見")
        expect(nav).to_be_visible(timeout=5000)

        # 已登入信號可見（進入首頁、未被遮蓋）
        expect(home.info_name).to_be_visible(timeout=10000)
