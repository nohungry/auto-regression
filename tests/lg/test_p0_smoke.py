"""
LG P0 Smoke Test — 大撈家娛樂城
每次 Release 必跑，保留核心健康度流程（登入、登出、首頁載入、錯誤登入）。

站點特性（probe 2026-06-05）：
- 框架：Nuxt (Vue)；登入為 modal 彈窗（非 /auth route，URL 不變）
- 進站公告彈窗（.dialog-container.w-full）會擋登入 CTA，登入流程內已先 dismiss
- avatar alt="" → 已登入信號用 .nav-bg .balance-color（餘額），非 img[alt="avatar"]
- avatar dropdown 由 click toggle（非 hover）；登出按鈕是 div
- 錯誤提示 toast：div[class*="z-[99999]"]（會 fade out，用屬性選擇器命中）
- 使用 `page` fixture（每個 test 獨立 context），autouse `auto_logout_after_test` 處理收尾
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from pages.factory import get_login_page_class, get_home_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lg")
HomePage = get_home_page_class("lg")


@pytest.mark.p0
@pytest.mark.lg
@pytest.mark.login
class TestLogin:
    """TC-LG-001 ~ TC-LG-002、TC-LG-005 ~ TC-LG-007：登入相關（含負向登入）"""

    def test_login_success(self, page: Page, site_config):
        """TC-LG-001：正常登入應成功，首頁顯示餘額與帳號名稱

        斷言策略：
        - .balance-color 可見（登入後才渲染，明確已登入信號）
        - .nav-bg 文字含登入帳號
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_invalid(self, page: Page, site_config):
        """TC-LG-002：錯誤密碼登入應失敗，顯示錯誤 toast 且 modal 仍開著

        斷言策略（probe 2026-06-05）：
        - 錯誤 toast div[class*="z-[99999]"] 出現（文字「提示密碼錯誤」，locale-sensitive
          故只驗 toast 出現，不驗文字）
        - 登入 modal 仍開著（帳號 input 仍可見），URL 停留首頁
        """
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)

        login.goto()
        login.dismiss_announcement()
        login.open_login_modal()

        # 填正確帳號 + 錯誤密碼
        login.username_input.scroll_into_view_if_needed()
        if sh: sh.capture(login.username_input, "fill_username_valid")
        login.username_input.fill(site_config.username)

        login.password_input.scroll_into_view_if_needed()
        if sh: sh.capture(login.password_input, "fill_password_wrong")
        login.password_input.fill("wrongpw123")

        login.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(login.submit_button, "click_login_submit_invalid")
        # dispatch_event：繞過 dev 過載時殘留公告 mask 對 submit 的 pointer 攔截（同 login_page）
        login.submit_button.dispatch_event("click")

        # 驗證錯誤 toast 出現
        expect(login.error_toast).to_be_visible(timeout=5000)
        # error_toast 綁 z-[99999] 高層容器（近全屏），紅框無鑑別度 → 整頁截圖
        if sh: sh.full_page("verify_error_toast_visible")

        # 登入 modal 仍開著（未成功）
        expect(login.username_input).to_be_visible(timeout=3000)

    def test_login_wrong_username(self, page: Page, site_config):
        """TC-LG-005：不存在帳號登入應失敗，顯示錯誤 toast 且 modal 仍開著

        斷言策略（對齊 test_login_invalid，依據 selector-explorer probe 2026-07-22）：
        - 錯誤 toast div[class*="z-[99999]"] 出現（文案 locale-sensitive，只驗容器出現不綁文字）
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
        # dispatch_event：繞過 dev 過載時殘留公告 mask 對 submit 的 pointer 攔截（同 login_page）
        login.submit_button.dispatch_event("click")

        expect(login.error_toast).to_be_visible(timeout=5000)
        # error_toast 綁 z-[99999] 高層容器（近全屏），紅框無鑑別度 → 整頁截圖
        if sh: sh.full_page("verify_error_toast_visible")

        expect(login.username_input).to_be_visible(timeout=3000)

    def test_login_empty_fields(self, page: Page, site_config):
        """TC-LG-006：空白帳密送出應失敗，顯示錯誤 toast 且 modal 仍開著

        斷言策略（依據 selector-explorer probe 2026-07-22）：
        - LG 無前端空欄位擋，空欄位送出打 API 回錯，錯誤呈現在與錯誤密碼相同的 z-[99999] toast
        - 錯誤 toast 出現（只驗容器）+ 登入 modal 仍開著
        """
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)

        login.goto()
        login.dismiss_announcement()
        login.open_login_modal()

        login.submit_button.scroll_into_view_if_needed()
        if sh: sh.capture(login.submit_button, "click_login_submit_empty")
        # dispatch_event：繞過 dev 過載時殘留公告 mask 對 submit 的 pointer 攔截（同 login_page）
        login.submit_button.dispatch_event("click")

        expect(login.error_toast).to_be_visible(timeout=5000)
        if sh: sh.full_page("verify_error_toast_visible")

        expect(login.username_input).to_be_visible(timeout=3000)

    def test_login_form_elements_exist(self, page: Page, site_config):
        """TC-LG-007：登入 modal 元素存在（帳號/密碼輸入框/送出按鈕）"""
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
@pytest.mark.lg
class TestLogout:
    """TC-LG-003：登出"""

    def test_logout(self, page: Page, site_config):
        """TC-LG-003：登入後登出，首頁登入 CTA 重新出現

        登出流程：click avatar 圓圈 → 右側 dropdown 滑入 → click 登出 div
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_logged_in()

        home.logout()
        home.verify_logged_out()


@pytest.mark.p0
@pytest.mark.lg
@pytest.mark.home
class TestHome:
    """TC-LG-004：首頁核心元素"""

    def test_home_loads(self, page: Page, site_config):
        """TC-LG-004：未登入直接開首頁應正常載入，進站公告出現，頂部 nav 含主要分類

        斷言策略：
        - 進站公告 .dialog-container.w-full 出現（首頁渲染健康度）
        - 頂部 nav ul.nav-item li 至少 4 項可見（locale-agnostic 結構驗證，
          不綁「熱門/電子/真人/捕魚」文案）
        """
        sh = get_screenshotter(page)

        # timeout=60s：dev 過載時首頁 domcontentloaded 偶爾 >30s 預設值（頁面會載入只是慢）
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        if sh: sh.full_page("verify_首頁載入完成")

        # 驗證進站公告彈窗渲染（async render，要 wait）
        announce = page.locator(".dialog-container.w-full").first
        try:
            announce.wait_for(state="visible", timeout=10000)
            if sh: sh.capture(announce, "verify_公告彈窗_present")
        except PlaywrightTimeoutError:
            # 公告可能被「今日不再顯示」記住而不出現；退而驗 nav 即可
            pass

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
