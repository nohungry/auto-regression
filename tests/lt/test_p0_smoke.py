"""
lt 站點 P0 Smoke Test（WAP 版，2026-04-21 rewrite）

每次 Release 必跑，驗證核心功能正常。WAP 設計要點：
- 無 hamburger / drawer — 會員入口為底部 tabbar「個人」→ /member-center
- Navbar 直接顯示 username pill + 餘額，不需開 drawer
- 首頁分類 `.cat-btn`（遊戲大廳 / 我的最愛 / 台灣真人 / 國際真人 / 更多）切換同頁內容，不改 URL
- 錯誤 dialog：`.dialog-wrapper` + `button.confirm-btn`（警告 + 錯誤文案 + 確定）

執行方式：
    .venv/bin/pytest tests/lt/test_p0_smoke.py -v
    .venv/bin/pytest tests/lt/test_p0_smoke.py -m p0 -v
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.lt.login_page import LoginPage
from pages.lt.home_page import HomePage
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter


# ─────────────────────────────────────────────────────────────
# 登入相關
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.lt
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

        # WAP 錯誤 dialog：.dialog-wrapper 含警告文案 + 確定按鈕
        error_dialog = page.locator('.dialog-wrapper').first
        error_dialog.wait_for(state="visible", timeout=8000)
        sh = get_screenshotter(page)
        if sh: sh.capture(error_dialog, "verify_錯誤提示彈窗")
        expect(error_dialog).to_contain_text("警告")
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

        error_dialog = page.locator('.dialog-wrapper').first
        error_dialog.wait_for(state="visible", timeout=8000)
        sh = get_screenshotter(page)
        if sh: sh.capture(error_dialog, "verify_錯誤提示彈窗")
        expect(error_dialog).to_contain_text("警告")
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
        if sh: sh.capture(login.username_input, "verify_仍在登入頁")
        expect(login.username_input).to_be_visible(timeout=3000)

    def test_logout(self, page: Page, site_config):
        """TC-005：可登出並回到未登入狀態"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_logged_in()
        home.logout()

        # 驗證 LaiTsai cookie 已消失
        cookies = page.context.cookies()
        cookie_names = [c["name"] for c in cookies]
        assert "LaiTsai" not in cookie_names, "登出後 LaiTsai cookie 仍存在"


# ─────────────────────────────────────────────────────────────
# 首頁核心（未登入）
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.lt
@pytest.mark.home
class TestHomePage:
    """TC-006 ~ TC-014：首頁核心元素"""

    def test_home_page_loads(self, page: Page, site_config):
        """TC-006：首頁可正常開啟"""
        login = LoginPage(page, site_config.url)
        login.goto()
        # 驗證 URL 包含 site_config 中設定的域名
        domain = site_config.url.split("//")[-1].rstrip("/")
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_首頁載入檢測")
        expect(page).to_have_url(re.compile(re.escape(domain)))

    def test_navigation_visible(self, page: Page, site_config):
        """TC-007：首頁主要分類 `.cat-btn` 顯示（遊戲大廳/我的最愛/台灣真人/國際真人/更多）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        for label in ["遊戲大廳", "我的最愛", "台灣真人", "國際真人", "更多"]:
            el = page.locator('.cat-btn', has_text=label).first
            expect(el).to_be_visible()
            if sh: sh.capture(el, f"verify_分類_{label}")

    def test_login_page_elements_exist(self, page: Page, site_config):
        """TC-008：登入頁元素存在（帳號/密碼/送出按鈕）"""
        set_locale(page, site_config.url)
        page.goto(site_config.url.rstrip("/") + "/login", wait_until="networkidle")
        sh = get_screenshotter(page)

        username_input = page.locator("input.login-input").nth(0)
        password_input = page.locator("input.login-input").nth(1)
        login_btn      = page.locator("button.btn-login")

        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()
        expect(login_btn).to_be_visible()
        if sh: sh.capture(username_input, "verify_帳號欄位")
        if sh: sh.capture(password_input, "verify_密碼欄位")
        if sh: sh.capture(login_btn,      "verify_登入按鈕")

    def test_login_cta_navigates_to_login_page(self, page: Page, site_config):
        """TC-009：首頁 tap「個人」tab 可進入登入頁（未登入狀態）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)

        login.open_login_form()

        if sh: sh.full_page("verify_進入登入頁")
        expect(page).to_have_url(re.compile(r"/login"), timeout=8000)
        expect(page.locator("input.login-input").nth(0)).to_be_visible()

    def test_balance_visible(self, page: Page, site_config):
        """TC-010：登入後 navbar 直接顯示帳號 pill 與餘額（無需開 drawer）"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        sh = get_screenshotter(page)

        # navbar 帳號 pill
        expect(home.navbar_login_pill).to_have_text(site_config.username, timeout=10000)
        if sh: sh.capture(home.navbar_login_pill, f"verify_navbar_帳號顯示_{site_config.username}")

        # navbar 餘額（非空）
        expect(home.navbar_balance).to_be_visible(timeout=5000)
        balance_text = (home.navbar_balance.text_content() or "").strip()
        if sh: sh.capture(home.navbar_balance, f"verify_navbar_餘額非空_{balance_text}")
        assert balance_text != "", "navbar 餘額欄位不應為空"

    @pytest.mark.skip(reason="WAP 版首頁已無公告跑馬燈（原 img[alt='Annt'] 不存在）；如日後 WAP 新增公告區需重寫")
    def test_announcement_marquee(self, page: Page, site_config):
        """TC-011：首頁公告跑馬燈有內容顯示（WAP 不適用）"""

    def test_hot_games_section(self, page: Page, site_config):
        """TC-012：首頁顯示遊戲區塊標題與遊戲卡片"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        sh = get_screenshotter(page)
        # WAP section 標題（可見至少一個）
        section_title = page.locator('.section-title').first
        expect(section_title).to_be_visible(timeout=5000)
        if sh: sh.capture(section_title, "verify_遊戲區塊標題")

        # 遊戲卡片（至少一張可見）
        game_card = page.locator('.game-slot').first
        if sh: sh.full_page("verify_遊戲卡片區塊")
        expect(game_card).to_be_visible()

    def test_casino_halls_visible(self, page: Page, site_config):
        """TC-013：首頁顯示所有真人廳館（T9真人、RC真人、DG真人、MT真人、歐博）"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        sh = get_screenshotter(page)
        # WAP 廳館以 img alt 呈現，locale-agnostic
        for hall in ["T9真人", "RC真人", "DG真人", "MT真人", "歐博"]:
            el = page.locator(f'img[alt="{hall}"]').first
            el.scroll_into_view_if_needed()
            if sh: sh.capture(el, f"verify_廳館_{hall}")
            expect(el).to_be_visible()

    def test_member_center_opens(self, page: Page, site_config):
        """TC-014：tap 底部「個人」tab 進入 /member-center 並顯示帳號資訊"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_member_center()
        if sh: sh.full_page("verify_member_center_開啟")
        expect(page).to_have_url(re.compile(r"/member-center"), timeout=8000)

        # 登出按鈕可見代表 member-center 已載入
        if sh: sh.capture(home.logout_btn, "verify_登出按鈕可見")
        expect(home.logout_btn).to_be_visible(timeout=5000)

        # 頁面有帳號文字
        username_hit = page.get_by_text(site_config.username, exact=False).first
        if sh: sh.capture(username_hit, f"verify_帳號顯示_{site_config.username}")
        expect(username_hit).to_be_visible(timeout=5000)


# ─────────────────────────────────────────────────────────────
# 導覽列分類切換（WAP 同頁 tab 切換，不改 URL）
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.lt
class TestNavigation:
    """TC-015：`.cat-btn` tap 可切換 `.cat-btn--selected`（需登入；我的最愛等分頁未登入無法切換）"""

    @pytest.mark.parametrize("nav_item", [
        "我的最愛",
        "台灣真人",
        "國際真人",
        "更多",
    ])
    def test_nav_cat_btn_switches_selected(self, page: Page, site_config, nav_item):
        """TC-015：tap `.cat-btn` 後該項目有 `.cat-btn--selected` class。
        用 dispatch_event("click") 規避「24小時客服」浮動按鈕對 pointer events 的攔截。
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)
        sh = get_screenshotter(page)

        nav = page.locator('.cat-btn', has_text=nav_item).first
        nav.scroll_into_view_if_needed()
        if sh: sh.capture(nav, f"click_分類_{nav_item}")
        nav.dispatch_event("click")

        if sh: sh.capture(nav, f"verify_分類已選中_{nav_item}")
        expect(nav).to_have_class(re.compile(r"cat-btn--selected"), timeout=5000)
