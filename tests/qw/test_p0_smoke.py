"""
QW P0 Smoke Test — LM來財娛樂城
每次 Release 必跑，保留核心健康度流程（登入、登出、首頁載入、錯誤登入）。

站點特性：
- 框架：Nuxt (Vue)；登入頁為 /auth（非 /login）
- 多語系：LaiBetLanguage cookie；selector 全部 CSS-based，不綁文案
- Avatar dropdown：hover 觸發（非 click）
- 使用 `page` fixture（每個 test 獨立 context），autouse `auto_logout_after_test` 處理收尾
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from pages.qw.login_page import LoginPage
from pages.qw.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p0
@pytest.mark.qw
@pytest.mark.login
class TestLogin:
    """TC-QW-001 ~ TC-QW-002：登入相關"""

    def test_login_success(self, page: Page, site_config):
        """TC-QW-001：正常登入應成功，首頁顯示帳號名稱

        斷言策略：
        - avatar 可見（代表已登入）
        - .avatar-trigger p 文字與登入帳號一致（驗字串相等，非只驗非空）
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.dismiss_any_popups()
        home.verify_login_success(site_config.username)

    def test_login_invalid(self, page: Page, site_config):
        """TC-QW-002：錯誤密碼登入應失敗，停留在 /auth 且顯示錯誤 toast

        斷言策略（probe 2026-05-29）：
        - URL 停留 /auth（未成功跳轉回首頁）
        - 錯誤 toast `.toast-msg--error` visible（locale-agnostic CSS class）
        """
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)

        login.goto()

        # 填入正確帳號 + 錯誤密碼
        login.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(login.username_input, "fill_username_valid")
        login.username_input.fill(site_config.username)

        login.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(login.password_input, "fill_password_wrong")
        login.password_input.fill("wrongpw123")

        login.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(login.submit_button, "click_login_submit_invalid")
        login.submit_button.click()

        # 驗證錯誤 toast 出現
        error_toast = page.locator('.toast-msg--error').first
        expect(error_toast).to_be_visible(timeout=5000)
        if sh: sh.capture(error_toast, "verify_error_toast_visible")

        # URL 應停留在 /auth（登入失敗未跳轉）
        assert "/auth" in page.url, f"預期停留 /auth，實際 URL：{page.url}"


@pytest.mark.p0
@pytest.mark.qw
class TestLogout:
    """TC-QW-003：登出"""

    def test_logout(self, page: Page, site_config):
        """TC-QW-003：登入後登出，首頁登入入口按鈕重新出現

        登出流程：hover avatar_trigger → dropdown 出現 → click button.avatar-menu__logout
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.dismiss_any_popups()
        home.verify_logged_in()

        home.logout()
        home.verify_logged_out()


@pytest.mark.p0
@pytest.mark.qw
@pytest.mark.home
class TestHome:
    """TC-QW-004：首頁核心元素"""

    def test_home_loads(self, page: Page, site_config):
        """TC-QW-004：未登入直接開首頁應正常載入，公告彈窗出現，頂部 nav 含主要分類

        斷言策略：
        - .popup-mask 或 .popup-close 出現代表公告彈窗正常渲染（登入前後都會出現）
        - 頂部 nav 含「首頁」「電子」「真人」「捕魚」（Nuxt 頁面 SSR/CSR 載入健康度）
        - 直接驗 CSS class selector，不綁語系文案（除「首頁」等固定繁中的導覽項之外；
          TODO：若 QW nav 多語系，改成 CSS-based selector 後請 selector-explorer 確認）
        """
        sh = get_screenshotter(page)

        # wait_until=domcontentloaded：QW 首頁背景 polling 不會 networkidle，
        # 改 DCL 後依靠後續 expect() 的 timeout 處理 hydration 等待
        page.goto(site_config.url, wait_until="domcontentloaded")
        if sh: sh.full_page("verify_首頁載入完成")

        # 驗證公告彈窗渲染（async render，要 wait）。任一 selector 可見就過
        popup_mask = page.locator('.popup-mask').first
        try:
            popup_mask.wait_for(state="visible", timeout=10000)
            if sh: sh.capture(popup_mask, "verify_popup_mask_present")
        except PlaywrightTimeoutError:
            popup_close = page.locator('.popup-close').first
            popup_close.wait_for(state="visible", timeout=3000)
            if sh: sh.capture(popup_close, "verify_popup_close_present")

        # 驗證頂部 nav 導覽項目存在
        # TODO：若 QW nav 為多語系，此處文案 selector 需改 CSS-based，
        #       請 selector-explorer probe 確認 nav item CSS class 後更新
        for nav_text in ["首頁", "電子", "真人", "捕魚"]:
            nav_el = page.locator(f"text={nav_text}").first
            nav_el.scroll_into_view_if_needed()
            if sh: sh.capture(nav_el, f"verify_nav_{nav_text}")
            expect(nav_el).to_be_visible(timeout=5000)
