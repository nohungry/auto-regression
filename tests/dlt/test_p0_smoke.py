"""
dlt 站點 P0 Smoke Test
每次 Release 必跑，驗證核心功能正常

對應 Node.js 版：

執行方式：
    .venv/bin/pytest tests/dlt/test_p0_smoke.py -v
    .venv/bin/pytest tests/dlt/test_p0_smoke.py -m p0 -v
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.dlt.login_page import LoginPage
from pages.dlt.home_page import HomePage
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter


# ─────────────────────────────────────────────────────────────
# 登入相關
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.dlt
@pytest.mark.login
class TestLogin:
    """TC-001 ~ TC-005：登入相關"""

    def test_login_success(self, page: Page, site_config):
        """TC-001：正常登入"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_wrong_password(self, page: Page, site_config):
        """TC-002：正確帳號 + 錯誤密碼應失敗，並出現錯誤提示彈窗"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        login.username_input.scroll_into_view_if_needed()
        login.username_input.fill(site_config.username)
        login.password_input.scroll_into_view_if_needed()
        login.password_input.fill("wrong_password_123")
        login.login_btn.scroll_into_view_if_needed()
        login.login_btn.click()

        # 錯誤彈窗以 shadow-dialog 樣式呈現，locale-agnostic
        error_dialog = page.locator('[class*="shadow-dialog"]')
        error_dialog.wait_for(state="attached", timeout=5000)
        sh = get_screenshotter(page)
        if sh: sh.capture(error_dialog, "verify_錯誤提示彈窗")
        expect(login.username_input).to_be_visible(timeout=5000)

    def test_login_wrong_username(self, page: Page, site_config):
        """TC-003：不存在帳號應失敗，並出現錯誤提示彈窗"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        login.username_input.scroll_into_view_if_needed()
        login.username_input.fill("nonexistent_user_xyz")
        login.password_input.scroll_into_view_if_needed()
        login.password_input.fill(site_config.password)
        login.login_btn.scroll_into_view_if_needed()
        login.login_btn.click()

        # 錯誤彈窗以 shadow-dialog 樣式呈現，locale-agnostic
        error_dialog = page.locator('[class*="shadow-dialog"]')
        error_dialog.wait_for(state="attached", timeout=5000)
        sh = get_screenshotter(page)
        if sh: sh.capture(error_dialog, "verify_錯誤提示彈窗")
        expect(login.username_input).to_be_visible(timeout=5000)

    def test_login_empty_fields(self, page: Page, site_config):
        """空白帳號密碼不應登入成功"""
        login = LoginPage(page, site_config.url)
        login.goto_login()

        login.login_btn.scroll_into_view_if_needed()
        sh = get_screenshotter(page)
        if sh: sh.capture(login.login_btn, "click_送出登入_空白欄位")
        login.login_btn.click()

        # 不應跳轉，仍在登入頁
        expect(login.username_input).to_be_visible(timeout=3000)
        if sh: sh.capture(login.username_input, "verify_仍在登入頁")

    def test_logout(self, logged_in_page: Page, site_config):
        """TC-005：可登出並回到未登入狀態"""
        home = HomePage(logged_in_page)
        home.logout()

        # 驗證 LaiTsai cookie 已消失
        cookies = logged_in_page.context.cookies()
        cookie_names = [c["name"] for c in cookies]
        assert "LaiTsai" not in cookie_names, \
            "登出後 LaiTsai cookie 仍存在"

        # 驗證登入按鈕重新出現
        expect(logged_in_page.get_by_role("button", name="登入")).to_be_visible()


# ─────────────────────────────────────────────────────────────
# 首頁核心（未登入）
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.dlt
@pytest.mark.home
class TestHomePage:
    """TC-006 ~ TC-014：首頁核心元素"""

    def test_home_page_loads(self, page: Page, site_config):
        """TC-006：首頁可正常開啟"""
        login = LoginPage(page, site_config.url)
        login.goto()
        expect(page).to_have_url(re.compile(r"dev-lt\.t9platform\.com"))
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_首頁正常開啟")

    def test_navigation_visible(self, page: Page, site_config):
        """TC-007：首頁主要分類顯示（熱門/真人/電子/捕魚）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        for label in ["熱門", "真人", "電子", "捕魚"]:
            el = page.get_by_text(label, exact=True).first
            expect(el).to_be_visible()
            if sh: sh.capture(el, f"verify_分類_{label}")

    def test_login_page_elements_exist(self, page: Page, site_config):
        """TC-008：登入頁元素存在（帳號/密碼/送出按鈕）"""
        set_locale(page, site_config.url)
        # lt 站 React 表單需等 networkidle，過早操作會導致 SPA 不跳轉
        page.goto(site_config.url.rstrip("/") + "/login", wait_until="networkidle")
        sh = get_screenshotter(page)

        # locale-agnostic：CSS selector 不依賴 placeholder 文案
        username_input = page.locator("input.input-style").nth(0)
        password_input = page.locator("input.input-style").nth(1)
        login_btn      = page.locator("button").first

        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()
        expect(login_btn).to_be_visible()
        if sh: sh.capture(username_input, "verify_帳號欄位")
        if sh: sh.capture(password_input, "verify_密碼欄位")
        if sh: sh.capture(login_btn,      "verify_登入按鈕")

    def test_login_cta_navigates_to_login_page(self, page: Page, site_config):
        """TC-009：首頁登入 CTA 可進入登入頁（登入表單出現）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)

        # 複用 POM 的 login_trigger_btn，避免在 test 層重複定義相同 locator
        if sh: sh.capture(login.login_trigger_btn, "click_登入CTA")
        # SPA pushState 不觸發 load event，改用 open_login_form 等輸入框出現
        login.open_login_form()

        # locale-agnostic：以 CSS selector 驗證帳號輸入框出現
        expect(page.locator("input.input-style").nth(0)).to_be_visible()
        if sh: sh.full_page("verify_進入登入頁")


    def test_balance_visible(self, logged_in_page: Page, site_config):
        """TC-010：登入後 navbar 餘額顯示（非空白）"""
        sh = get_screenshotter(logged_in_page)
        # navbar 內有兩個 img[alt="Balance"]：nth(0) = mobile（lg:hidden，0×0），nth(1) = desktop（visible）
        # drawer 的 Balance icon 在 navbar 元素外，不在此 locator 範圍內
        navbar = logged_in_page.locator('[class*="bg-navbar"]')
        balance_icon = navbar.locator('img[alt="Balance"]').nth(1)
        expect(balance_icon).to_be_visible(timeout=5000)
        balance_text = balance_icon.locator('..').locator('p').text_content()
        assert balance_text and balance_text.strip(), "餘額顯示為空"
        if sh: sh.capture(balance_icon, "verify_餘額顯示")

    def test_announcement_marquee(self, logged_in_page: Page, site_config):
        """TC-011：首頁公告跑馬燈有內容顯示"""
        sh = get_screenshotter(logged_in_page)
        announcement = logged_in_page.locator('img[alt="Annt"]')
        expect(announcement).to_be_visible(timeout=5000)
        # 公告文字內容用 img[alt="Annt"] 的父容器確認有文字，locale-agnostic
        marquee_container = announcement.locator('..').locator('..')
        expect(marquee_container).not_to_be_empty()
        if sh: sh.capture(announcement, "verify_公告跑馬燈")

    def test_hot_games_section(self, logged_in_page: Page, site_config):
        """TC-012：首頁顯示「熱門」區塊且有遊戲卡片"""
        sh = get_screenshotter(logged_in_page)
        hot_label = logged_in_page.get_by_text("熱門", exact=True).first
        expect(hot_label).to_be_visible(timeout=5000)
        if sh: sh.capture(hot_label, "verify_熱門區塊標題")
        game_cards = logged_in_page.locator('img[alt="Hot"]')
        expect(game_cards.first).to_be_visible()
        if sh: sh.full_page("verify_熱門遊戲區塊")

    def test_casino_halls_visible(self, logged_in_page: Page, site_config):
        """TC-013：首頁顯示所有真人廳館（T9真人、RC真人、DG真人、MT真人、歐博）"""
        sh = get_screenshotter(logged_in_page)
        for hall in ["T9真人", "RC真人", "DG真人", "MT真人", "歐博"]:
            el = logged_in_page.get_by_text(hall, exact=True).first
            expect(el).to_be_visible()
            if sh: sh.capture(el, f"verify_廳館_{hall}")

    def test_member_drawer_opens(self, logged_in_page: Page, site_config):
        """TC-014：會員 drawer 可正常開啟並顯示帳號名稱"""
        home = HomePage(logged_in_page)
        sh = get_screenshotter(logged_in_page)
        home.open_member_drawer()
        # drawer 內帳號 p 有 text-xl class，navbar 帳號 p 沒有，以此區分 drawer 與 navbar
        username_el = logged_in_page.locator('p[class*="text-xl"]', has_text=site_config.username).first
        expect(username_el).to_be_visible(timeout=5000)
        if sh: sh.capture(username_el, f"verify_drawer_帳號顯示_{site_config.username}")


# ─────────────────────────────────────────────────────────────
# 導覽列分類頁跳轉
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.dlt
class TestNavigation:
    """TC-015：分類頁導向"""

    @pytest.mark.parametrize("nav_item,expected_path", [
        ("熱門", "/Categories/hot"),
        ("真人", "/Categories/casino"),
        ("電子", "/Categories/slots"),
        ("捕魚", "/Categories/fishing"),
    ])
    def test_nav_to_category(self, page: Page, site_config, nav_item, expected_path):
        """TC-015：首頁分類可導向對應頁面"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        nav = page.get_by_text(nav_item, exact=True).first
        nav.scroll_into_view_if_needed()
        if sh: sh.capture(nav, f"click_分類_{nav_item}")
        nav.click()
        expect(page).to_have_url(re.compile(re.escape(expected_path)), timeout=8000)
        if sh: sh.full_page(f"verify_跳轉至_{nav_item}頁")
