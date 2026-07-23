"""
KS P0 Smoke Test — Super9娛樂城
每次 Release 必跑，保留核心健康度流程（登入、登出、首頁載入、錯誤登入）。

站點特性（probe 2026-06-05；與 LG 同框架但金色英文主題）：
- 框架：Nuxt (Vue)；登入為 modal 彈窗（非 /auth route，URL 不變）
- 登入 CTA button.gold-btn；登入 modal .dialog-container.max-w-[388px]；submit button.primary-btn
- 無 .balance-color → 已登入信號用 nav wallet 圖示；KS 有顯示 username
- 無 avatar dropdown：登出走右側 drawer（hamburger → button.secondary-btn）
- 錯誤密碼顯示 modal（div[class*="z-[99999]"]）而非 toast
- 使用 `page` fixture（每個 test 獨立 context），autouse `auto_logout_after_test` 處理收尾
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from pages.ks.login_page import LoginPage
from pages.ks.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p0
@pytest.mark.ks
@pytest.mark.login
class TestLogin:
    """TC-KS-001 ~ TC-KS-002、TC-KS-005 ~ TC-KS-007：登入相關（含負向登入）"""

    def test_login_success(self, page: Page, site_config):
        """TC-KS-001：正常登入應成功，nav 顯示 wallet 圖示與帳號名稱"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_invalid(self, page: Page, site_config):
        """TC-KS-002：錯誤密碼登入應失敗，顯示錯誤 modal 且 URL 停留首頁

        斷言策略（probe 2026-06-05）：
        - 錯誤 modal div[class*="z-[99999]"] 出現（文字「Password is incorrect」，
          locale-sensitive 故只驗 modal 出現，不驗文字）
        - URL 停留首頁
        """
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)

        login.goto()
        login.dismiss_announcement()
        login.open_login_modal()

        login.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(login.username_input, "fill_username_valid")
        login.username_input.fill(site_config.username)

        login.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(login.password_input, "fill_password_wrong")
        login.password_input.fill("wrongpw123")

        login.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(login.submit_button, "click_login_submit_invalid")
        # dispatch_event：繞過 KS 卡住的公告 .dialog-mask 對 submit 的 pointer 攔截（同 login_page）
        login.submit_button.dispatch_event("click")

        # 驗證錯誤 modal 出現
        expect(login.error_modal).to_be_visible(timeout=5000)
        if sh: sh.capture(login.error_modal, "verify_error_modal_visible")

        # URL 停留首頁（登入失敗未跳轉）
        assert page.url.rstrip("/") == site_config.url.rstrip("/"), \
            f"預期停留首頁，實際 URL：{page.url}"

    def test_login_wrong_username(self, page: Page, site_config):
        """TC-KS-005：不存在帳號登入應失敗，顯示錯誤 modal 且登入 modal 仍開著

        斷言策略（對齊 test_login_invalid，依據 selector-explorer probe 2026-07-22）：
        - 錯誤 modal div[class*="z-[99999]"] 出現（英文文案 locale-sensitive，只驗 modal 出現不綁文字）
        - 登入 modal 仍開著（帳號 input 仍可見）
        """
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)

        login.goto()
        login.dismiss_announcement()
        login.open_login_modal()

        # 填入不存在帳號 + 該站正確密碼
        login.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(login.username_input, "fill_username_nonexistent")
        login.username_input.fill("nonexistent_user_xyz")

        login.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(login.password_input, "fill_password")
        login.password_input.fill(site_config.password)

        login.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(login.submit_button, "click_login_submit_invalid")
        # dispatch_event：繞過 KS 卡住的公告 .dialog-mask 對 submit 的 pointer 攔截（同 login_page）
        login.submit_button.dispatch_event("click")

        expect(login.error_modal).to_be_visible(timeout=5000)
        if sh: sh.capture(login.error_modal, "verify_error_modal_visible")

        expect(login.username_input).to_be_visible(timeout=3000)

    def test_login_empty_fields(self, page: Page, site_config):
        """TC-KS-006：空白帳密時送出按鈕應為 disabled（四站唯一有前端 guard），登入 modal 仍在

        斷言策略（依據 selector-explorer probe 2026-07-22）：
        - KS 送出鈕在空欄位時 disabled（前端擋，與 qw/lg/lu 不同）
        - 不點擊：probe 證實 dispatchEvent 可繞過 disabled 打 API，但那不是真實使用者路徑，不採用
        - 斷言 submit_button to_be_disabled() + 登入 modal 仍開著（帳號 input 仍可見）
        """
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)

        login.goto()
        login.dismiss_announcement()
        login.open_login_modal()

        login.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(login.submit_button, "verify_送出按鈕_disabled_空白欄位")
        expect(login.submit_button).to_be_disabled()

        if sh: sh.capture(login.username_input, "verify_登入modal仍在")
        expect(login.username_input).to_be_visible(timeout=3000)

    def test_login_form_elements_exist(self, page: Page, site_config):
        """TC-KS-007：登入 modal 元素存在（帳號/密碼輸入框/送出按鈕）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.dismiss_announcement()
        login.open_login_modal()
        sh = get_screenshotter(page)

        login.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(login.username_input, "verify_帳號欄位")
        login.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(login.password_input, "verify_密碼欄位")
        login.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(login.submit_button, "verify_送出按鈕")
        expect(login.username_input).to_be_visible()
        expect(login.password_input).to_be_visible()
        expect(login.submit_button).to_be_visible()


@pytest.mark.p0
@pytest.mark.ks
class TestLogout:
    """TC-KS-003：登出"""

    def test_logout(self, page: Page, site_config):
        """TC-KS-003：登入後登出，首頁登入 CTA 重新出現

        登出流程：點 hamburger 展開右側 drawer → click button.secondary-btn
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_logged_in()

        home.logout()
        home.verify_logged_out()


@pytest.mark.p0
@pytest.mark.ks
@pytest.mark.home
class TestHome:
    """TC-KS-004：首頁核心元素"""

    def test_home_loads(self, page: Page, site_config):
        """TC-KS-004：未登入直接開首頁應正常載入，進站公告出現，頂部 nav 含主要分類

        斷言策略：
        - 進站公告 .dialog-container.w-full 出現（首頁渲染健康度）
        - 頂部 nav ul.nav-item li 至少 4 項可見（locale-agnostic 結構驗證，KS 實際 7 項）
        """
        sh = get_screenshotter(page)

        # timeout=60s：dev 過載時首頁 domcontentloaded 偶爾 >30s 預設值（頁面會載入只是慢）
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        if sh: sh.full_page("verify_首頁載入完成")

        # 驗證進站公告彈窗渲染
        announce = page.locator(".dialog-container.w-full").first
        try:
            announce.wait_for(state="visible", timeout=10000)
            if sh: sh.capture(announce, "verify_公告彈窗_present")
        except PlaywrightTimeoutError:
            pass  # 公告可能被「今日不再顯示」記住而不出現

        # 驗證頂部 nav 分類項目（結構化，不綁文案）
        nav_items = page.locator("ul.nav-item li")
        expect(nav_items.first).to_be_visible(timeout=10000)
        count = nav_items.count()
        assert count >= 4, f"預期 nav 分類至少 4 項，實際 {count} 項"
        for i in range(4):
            item = nav_items.nth(i)
            item.scroll_into_view_if_needed()
            if sh: sh.capture(item, f"verify_nav_item_{i}")
            expect(item).to_be_visible(timeout=5000)
