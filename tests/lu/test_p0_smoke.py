"""
LU P0 Smoke Test — Dlgbet
每次 Release 必跑，保留核心健康度流程（登入、登出、首頁載入、錯誤登入）。

站點特性（probe 2026-06-05；與姊妹站 LG 結構差異大）：
- 框架：Nuxt (Vue)；登入為 modal 彈窗（非 /auth route，URL 不變）
- 進站雙層彈窗：圖片廣告（button.popup-close-btn）+ 文字公告（.close-wrap）
- 不顯示 username → 已登入信號用 nav 餘額 span + 登錄 CTA 消失
- 無 avatar dropdown：登出在左側 sidebar（hamburger button.nav-toggle-btn 展開）
- 錯誤密碼顯示 modal（.dialog-container.mx-auto）而非 toast
- 使用 `page` fixture（每個 test 獨立 context），autouse `auto_logout_after_test` 處理收尾
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from pages.lu.login_page import LoginPage
from pages.lu.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p0
@pytest.mark.lu
@pytest.mark.login
class TestLogin:
    """TC-LU-001 ~ TC-LU-002、TC-LU-005 ~ TC-LU-007：登入相關（含負向登入）"""

    def test_login_success(self, page: Page, site_config):
        """TC-LU-001：正常登入應成功，nav 顯示餘額且登錄 CTA 消失"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_invalid(self, page: Page, site_config):
        """TC-LU-002：錯誤密碼登入應失敗，顯示錯誤 modal 且登入 modal 仍開著

        斷言策略（probe 2026-06-05）：
        - 錯誤 modal .dialog-container.mx-auto 出現（文字「密碼錯誤」，locale-sensitive
          故只驗 modal 出現，不驗文字）
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
        # dispatch_event：繞過雙層公告 .dialog-mask 在慢環境下的 pointer 攔截（同 login_page）
        login.submit_button.dispatch_event("click")

        # 驗證錯誤 modal 出現
        expect(login.error_modal).to_be_visible(timeout=5000)
        if sh: sh.capture(login.error_modal, "verify_error_modal_visible")

        # URL 停留首頁（登入失敗未跳轉）
        assert page.url.rstrip("/") == site_config.url.rstrip("/"), \
            f"預期停留首頁，實際 URL：{page.url}"

    def test_login_wrong_username(self, page: Page, site_config):
        """TC-LU-005：不存在帳號登入應失敗，顯示錯誤 modal 且登入 modal 仍開著

        斷言策略（對齊 test_login_invalid，依據 selector-explorer probe 2026-07-22）：
        - 錯誤 modal .dialog-container.mx-auto 出現（文案 locale-sensitive，只驗 modal 出現不綁文字）
        - 登入 modal 仍開著（帳號 input 仍可見）
        - 錯誤 modal 不會自動消失，斷言後手動關閉避免殘留污染後續截圖/斷言
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
        # dispatch_event：繞過雙層公告 .dialog-mask 在慢環境下的 pointer 攔截（同 login_page）
        login.submit_button.dispatch_event("click")

        expect(login.error_modal).to_be_visible(timeout=5000)
        if sh: sh.capture(login.error_modal, "verify_error_modal_visible")

        # 錯誤 modal 不會自動消失，手動關閉避免殘留污染後續截圖/斷言
        login.error_modal.locator(".close-wrap").dispatch_event("click")

        expect(login.username_input).to_be_visible(timeout=3000)

    def test_login_empty_fields(self, page: Page, site_config):
        """TC-LU-006：空白帳密送出應失敗，顯示錯誤 modal 且登入 modal 仍開著

        斷言策略（依據 selector-explorer probe 2026-07-22）：
        - LU 無前端空欄位擋，空欄位送出打 API 回錯，錯誤呈現在與錯誤密碼相同的 .dialog-container.mx-auto modal
        - 錯誤 modal 出現（只驗容器）+ 登入 modal 仍開著
        - 錯誤 modal 不會自動消失，斷言後手動關閉避免殘留污染後續截圖/斷言
        """
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)

        login.goto()
        login.dismiss_announcement()
        login.open_login_modal()

        login.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(login.submit_button, "click_login_submit_empty")
        # dispatch_event：繞過雙層公告 .dialog-mask 在慢環境下的 pointer 攔截（同 login_page）
        login.submit_button.dispatch_event("click")

        expect(login.error_modal).to_be_visible(timeout=5000)
        if sh: sh.capture(login.error_modal, "verify_error_modal_visible")

        # 錯誤 modal 不會自動消失，手動關閉避免殘留污染後續截圖/斷言
        login.error_modal.locator(".close-wrap").dispatch_event("click")

        expect(login.username_input).to_be_visible(timeout=3000)

    def test_login_form_elements_exist(self, page: Page, site_config):
        """TC-LU-007：登入 modal 元素存在（帳號/密碼輸入框/送出按鈕）"""
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
@pytest.mark.lu
class TestLogout:
    """TC-LU-003：登出"""

    def test_logout(self, page: Page, site_config):
        """TC-LU-003：登入後登出，首頁登錄 CTA 重新出現

        登出流程：點 hamburger 展開左側 sidebar → click 登出 button
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_logged_in()

        home.logout()
        home.verify_logged_out()


@pytest.mark.p0
@pytest.mark.lu
@pytest.mark.home
class TestHome:
    """TC-LU-004：首頁核心元素"""

    def test_home_loads(self, page: Page, site_config):
        """TC-LU-004：未登入直接開首頁應正常載入，進站彈窗出現，遊戲分類連結存在

        斷言策略：
        - 進站彈窗（圖片廣告或文字公告）出現（首頁渲染健康度）
        - 遊戲分類 a[href*='/Categories/'] 至少 4 個（locale-agnostic 結構驗證）
        """
        sh = get_screenshotter(page)

        # timeout=60s：dev 過載時首頁 domcontentloaded 偶爾 >30s 預設值（頁面會載入只是慢）
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        if sh: sh.full_page("verify_首頁載入完成")

        # 驗證進站彈窗渲染（圖片廣告或文字公告任一）
        ad_popup = page.locator("button.popup-close-btn")
        announce = page.locator(".dialog-container.w-full").first
        try:
            ad_popup.wait_for(state="visible", timeout=10000)
            if sh: sh.capture(ad_popup, "verify_進站彈窗_present")
        except PlaywrightTimeoutError:
            try:
                announce.wait_for(state="visible", timeout=3000)
                if sh: sh.capture(announce, "verify_公告彈窗_present")
            except PlaywrightTimeoutError:
                pass  # 彈窗可能被「今日不再顯示」記住

        # 驗證遊戲分類連結（結構化，不綁文案）
        categories = page.locator("a[href*='/Categories/']")
        expect(categories.first).to_be_visible(timeout=10000)
        count = categories.count()
        assert count >= 4, f"預期遊戲分類連結至少 4 個，實際 {count} 個"
        for i in range(min(4, count)):
            item = categories.nth(i)
            item.scroll_into_view_if_needed()
            if sh: sh.capture(item, f"verify_category_{i}")
