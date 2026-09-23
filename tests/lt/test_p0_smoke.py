"""
lt 站點 P0 Smoke Test（LM來財信用網；2026-09-13 rewrite，第三次換版）

dev-lt 自 2026-07-23 起改用與 RC（王老吉）相同的前台模板。本檔依 2026-09-13 實機
probe 重寫（probe 筆記：dev-notes/lt-redesign-v3-probe-2026-09-13.md）。

新版設計要點：
- 登入為獨立路由 `/login`（首頁 navbar `button.nav-login-btn` 進入），非 modal
- 登入送出後出現「用戶協議」彈窗（`.dialog-container button.black-btn` 確定）
- 登入完成＝離開 /login 且 DLT cookie 存在
- 已登入 navbar：帳號 `p.name-shadow`、信用額度 `.coin-wrap-bg span`、頭像 `img[alt="avatar"]`
- 登出：頭像下拉 → 登出（HomePage.logout()）
- 個人中心＝側欄 `.sidebar-item.user` 開的 `.dialog-mask` 彈窗（含帳號欄位）
- 錯誤提示彈窗 `button.toast-confirm-btn`（密碼錯誤 / 帳號不存在）；空欄位則前端擋下無彈窗
- 首頁有 RC 型進站公告 `.popup-announcement-mask`（POM 內已清）

執行方式：
    .venv/bin/pytest tests/lt/test_p0_smoke.py -v
    .venv/bin/pytest tests/lt/test_p0_smoke.py -m p0 -v
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class, get_home_page_class
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lt")
HomePage = get_home_page_class("lt")


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

    @pytest.mark.no_toast_observer
    def test_login_wrong_password(self, page: Page, site_config):
        """TC-002：正確帳號 + 錯誤密碼應失敗，並出現「密碼錯誤」提示彈窗

        no_toast_observer：停用根 conftest 的全域 MutationObserver（它會秒關所有
        toast-confirm-btn），否則斷言不到彈窗（與 RC 同作法）。
        """
        login = LoginPage(page, site_config.url)
        login.goto_login()
        login.login(site_config.username, "wrong_password_123", expect_success=False)

        sh = get_screenshotter(page)
        error_msg = page.locator("p", has_text="密碼錯誤")
        if sh: sh.capture(login.error_confirm_btn, "verify_錯誤提示彈窗_確定按鈕")
        if sh: sh.capture(error_msg, "verify_密碼錯誤訊息")
        expect(login.error_confirm_btn).to_be_visible(timeout=10000)
        expect(error_msg).to_be_visible()
        expect(login.username_input).to_be_visible(timeout=5000)

    @pytest.mark.no_toast_observer
    def test_login_wrong_username(self, page: Page, site_config):
        """TC-003：不存在帳號應失敗，並出現「帳號不存在」提示彈窗

        no_toast_observer：同 test_login_wrong_password。
        """
        login = LoginPage(page, site_config.url)
        login.goto_login()
        login.login("nonexistent_user_xyz", site_config.password, expect_success=False)

        sh = get_screenshotter(page)
        error_msg = page.locator("p", has_text="帳號不存在")
        if sh: sh.capture(login.error_confirm_btn, "verify_錯誤提示彈窗_確定按鈕")
        if sh: sh.capture(error_msg, "verify_帳號不存在訊息")
        expect(login.error_confirm_btn).to_be_visible(timeout=10000)
        expect(error_msg).to_be_visible()
        expect(login.username_input).to_be_visible(timeout=5000)

    def test_login_empty_fields(self, page: Page, site_config):
        """TC-004：空白帳號密碼不應登入成功（probe 2026-09-13：前端擋下，無彈窗、停在 /login）"""
        login = LoginPage(page, site_config.url)
        login.goto_login()

        sh = get_screenshotter(page)
        if sh: sh.capture(login.login_btn, "click_送出登入_空白欄位")
        login.login_btn.click()

        if sh: sh.capture(login.username_input, "verify_仍在登入頁")
        expect(login.username_input).to_be_visible(timeout=5000)
        expect(page).to_have_url(re.compile(r"/login"))

    def test_logout(self, page: Page, site_config):
        """TC-005：可登出並回到未登入狀態（DLT cookie 被清除）"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_logged_in()
        home.logout()

        cookie_names = [c["name"] for c in page.context.cookies()]
        assert "DLT" not in cookie_names, "登出後 DLT cookie 仍存在"


# ─────────────────────────────────────────────────────────────
# 首頁核心
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
        domain = site_config.url.split("//")[-1].rstrip("/")
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_首頁載入檢測")
        expect(page).to_have_url(re.compile(re.escape(domain)))

    def test_navigation_visible(self, page: Page, site_config):
        """TC-007：navbar 導覽列顯示主要分類入口（真人 / 電子 / 捕魚）。

        2026-09-13 換版：改為 `ul.nav-item` 連結，以 href 定位（locale-agnostic），
        不綁文案（LT 為多語系站）。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        for label, route in [("真人", "casino"), ("電子", "slots"), ("捕魚", "fishing")]:
            el = page.locator(f"ul.nav-item a[href^='/Categories/{route}']").first
            el.scroll_into_view_if_needed()
            if sh: sh.capture(el, f"verify_導覽列_{label}")
            expect(el).to_be_visible()

    def test_login_page_elements_exist(self, page: Page, site_config):
        """TC-008：登入頁元素存在（帳號 input / 密碼 input / 登入按鈕）"""
        set_locale(page, site_config.url)
        page.goto(site_config.url.rstrip("/") + "/login", wait_until="domcontentloaded")
        sh = get_screenshotter(page)

        username_input = page.locator("input.input-style[type='text']").first
        password_input = page.locator("input.input-style[type='password']").first
        login_btn = page.locator("button.primary-btn").first

        username_input.wait_for(state="visible", timeout=15000)
        if sh: sh.capture(username_input, "verify_帳號欄位")
        if sh: sh.capture(password_input, "verify_密碼欄位")
        if sh: sh.capture(login_btn,      "verify_登入按鈕")
        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()
        expect(login_btn).to_be_visible()

    def test_login_cta_navigates_to_login_page(self, page: Page, site_config):
        """TC-009：首頁 navbar「登入」CTA 可進入 /login（未登入狀態）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)

        login.open_login_form()

        if sh: sh.full_page("verify_進入登入頁")
        expect(page).to_have_url(re.compile(r"/login"), timeout=10000)
        expect(login.username_input).to_be_visible()

    def test_balance_visible(self, page: Page, site_config):
        """TC-010：登入後 navbar 顯示帳號與信用額度。

        信用額度為動態值，只驗「非空」不寫死數值；截圖 label 帶當前值僅供人工 review。
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        sh = get_screenshotter(page)

        expect(home.navbar_login_pill).to_have_text(site_config.username, timeout=15000)
        if sh: sh.capture(home.navbar_login_pill, f"verify_navbar帳號_{site_config.username}")

        expect(home.navbar_balance).to_be_visible(timeout=10000)
        balance_text = (home.navbar_balance.text_content() or "").strip()
        if sh: sh.capture(home.navbar_balance, f"verify_navbar信用額度非空_{balance_text}")
        assert balance_text != "", "navbar 信用額度欄位不應為空"

    @pytest.mark.skip(reason="首頁無公告跑馬燈元件（probe 2026-06-26 確認、2026-09-13 換版後複驗仍無）；公告入口為右側側欄 .sidebar-item.announce，由 feature 層涵蓋。此 marquee 測試永久不適用。")
    def test_announcement_marquee(self, page: Page, site_config):
        """TC-011：[OBSOLETE] 首頁公告跑馬燈 — 已移除，公告改隸側欄"""

    def test_hot_games_section(self, page: Page, site_config):
        """TC-012：首頁顯示區塊標題與遊戲卡片。

        2026-09-13 換版：區塊標題改為 `.group > p.tip-single.whitespace-nowrap`
        （來財獨家/活動專區/熱門遊戲/最新遊戲/爆分精選），舊 `span.category-title`
        已不存在。標題文案隨語系變動，故以結構定位、不綁文字，只驗 ≥1 個可見；
        卡片仍為 `.grid > .relative.cursor-pointer`（張數隨後台設定變動，只驗 ≥1）。
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        sh = get_screenshotter(page)
        section_titles = page.locator(".group > p.tip-single.whitespace-nowrap")
        section_title = section_titles.first
        section_title.scroll_into_view_if_needed()
        if sh: sh.capture(section_title, f"verify_首頁區塊標題_count{section_titles.count()}")
        expect(section_title).to_be_visible(timeout=10000)

        game_cards = page.locator(".grid > .relative.cursor-pointer")
        card = game_cards.first
        card.scroll_into_view_if_needed()
        if sh: sh.capture(card, f"verify_遊戲卡片_count{game_cards.count()}")
        expect(card).to_be_visible(timeout=10000)

    def test_casino_halls_visible(self, page: Page, site_config):
        """TC-013：首頁顯示真人廳館卡片。

        2026-09-23 複驗：廳館圖已改為 `/img/casino/<hall>.webp`（t9/ob/dg/rc/mt），
        舊 `img[src*="HomePageImgcasino_"]` 命中 0。改以**路徑前綴**定位而非廳名，
        廳別與廳數都會隨後台設定變動（本次複驗 rc 廳即重新上架），故只驗 ≥1 張可見。
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        sh = get_screenshotter(page)
        halls = page.locator("img[src^='/img/casino/']")
        hall = halls.first
        hall.scroll_into_view_if_needed()
        if sh: sh.capture(hall, f"verify_真人廳館卡片_count{halls.count()}")
        if sh: sh.full_page("verify_真人廳館_整體版面")
        expect(hall).to_be_visible(timeout=10000)

    def test_member_center_opens(self, page: Page, site_config):
        """TC-014：側欄「個人資訊」可開啟會員彈窗並顯示登入帳號。

        2026-09-13 換版：會員中心改為側欄 `.sidebar-item.user` 開的 `.dialog-mask` 彈窗
        （舊底部 tabbar + `.dialog-mask-full` panel 已移除），URL 維持 `/`。
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_member_center()
        if sh: sh.full_page("verify_個人資訊彈窗_開啟")
        expect(home.member_panel).to_be_visible(timeout=10000)

        if sh: sh.capture(home.member_account_input, f"verify_彈窗帳號欄_{site_config.username}")
        expect(home.member_account_input).to_have_value(site_config.username, timeout=10000)

        if sh: sh.capture(home.member_panel_logout_btn, "verify_彈窗登出按鈕可見")
        expect(home.member_panel_logout_btn).to_be_visible(timeout=5000)


# ─────────────────────────────────────────────────────────────
# 導覽列分類切換
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.lt
class TestNavigation:
    """TC-015：導覽列分類入口可跳轉到對應分類頁"""

    @pytest.mark.parametrize("nav_item,route", [
        ("真人", "casino"),
        ("電子", "slots"),
        ("捕魚", "fishing"),
    ])
    def test_nav_item_navigates_to_category(self, page: Page, site_config, nav_item, route):
        """TC-015：點 navbar 分類入口後 URL 進入對應 /Categories/<route>。

        2026-09-13 換版：舊 `.cat-btn--selected` 切換機制已不存在，改為 navbar 連結導覽；
        以 href 定位（locale-agnostic），不綁文案。
        """
        login = LoginPage(page, site_config.url)
        login.goto()

        home = HomePage(page)
        sh = get_screenshotter(page)
        home.click_nav_item(nav_item)

        if sh: sh.full_page(f"verify_分類頁_{nav_item}")
        expect(page).to_have_url(re.compile(re.escape(f"/Categories/{route}")), timeout=15000)
