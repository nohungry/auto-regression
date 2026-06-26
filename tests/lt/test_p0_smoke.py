"""
lt 站點 P0 Smoke Test（desktop responsive 版，2026-05-18 rewrite）

每次 Release 必跑，驗證核心功能正常。Desktop 設計要點（換版後）：
- 無 hamburger / drawer — 會員入口為底部 tabbar「個人」→ 開 .dialog-mask-full overlay panel
- Navbar 已登入顯示 username pill (.user-info-bg p.tip-single) + 信用額度 (.coin-wrap-bg span)
- 登入完成判斷：DLT cookie 存在；page.url 不可靠（Nuxt pushState 不更新 url 對象）
- 個人中心非獨立路由（無 /member-center），URL 維持 /
- 錯誤 dialog 確定按鈕：button.toast-confirm-btn（替代舊 button.confirm-btn）
- 舊 .cat-btn 分類 tab 已消失，改為 swipe sections (span.category-title)

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
        # 用 dispatch_event 觸發 Vue handler（與 LoginPage.login() 一致）
        login.login_btn.dispatch_event("click")

        # 錯誤 dialog：button.toast-confirm-btn 為穩定 anchor
        login.error_confirm_btn.wait_for(state="visible", timeout=8000)
        sh = get_screenshotter(page)
        if sh: sh.capture(login.error_confirm_btn, "verify_錯誤提示彈窗_確定按鈕")
        expect(login.username_input).to_be_visible(timeout=5000)

    def test_login_wrong_username(self, page: Page, site_config):
        """TC-003：不存在帳號應失敗，並出現錯誤提示彈窗"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        login.username_input.scroll_into_view_if_needed()
        login.username_input.fill("nonexistent_user_xyz")
        login.password_input.scroll_into_view_if_needed()
        login.password_input.fill(site_config.password)
        login.login_btn.dispatch_event("click")

        login.error_confirm_btn.wait_for(state="visible", timeout=8000)
        sh = get_screenshotter(page)
        if sh: sh.capture(login.error_confirm_btn, "verify_錯誤提示彈窗_確定按鈕")
        expect(login.username_input).to_be_visible(timeout=5000)

    def test_login_empty_fields(self, page: Page, site_config):
        """空白帳號密碼不應登入成功"""
        login = LoginPage(page, site_config.url)
        login.goto_login()

        sh = get_screenshotter(page)
        if sh: sh.capture(login.login_btn, "click_送出登入_空白欄位")
        login.login_btn.dispatch_event("click")

        # 不應跳轉，仍在登入頁
        if sh: sh.capture(login.username_input, "verify_仍在登入頁")
        expect(login.username_input).to_be_visible(timeout=3000)

    def test_logout(self, page: Page, site_config):
        """TC-005：可登出並回到未登入狀態（DLT cookie 被清除）"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_logged_in()
        home.logout()

        # 驗證 DLT cookie 已消失（登入成功標記）
        cookies = page.context.cookies()
        cookie_names = [c["name"] for c in cookies]
        assert "DLT" not in cookie_names, "登出後 DLT cookie 仍存在"


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
        """TC-007：首頁顯示主要 section 標題（來財獨家 / 爆分精選 / 活動專區）。

        2026-05-18 換版：舊 .cat-btn 分類 tab 已消失，改為 swipe sections。
        改驗 span.category-title 文字呈現（未登入即可見）。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        for label in ["來財獨家", "爆分精選", "活動專區"]:
            el = page.locator("span.category-title", has_text=label).first
            el.scroll_into_view_if_needed()
            expect(el).to_be_visible()
            if sh: sh.capture(el, f"verify_section_{label}")

    def test_login_page_elements_exist(self, page: Page, site_config):
        """TC-008：登入頁元素存在（帳號 input / 密碼 input / 會員登入按鈕）"""
        set_locale(page, site_config.url)
        page.goto(site_config.url.rstrip("/") + "/login", wait_until="networkidle")
        sh = get_screenshotter(page)

        username_input = page.locator("input.input-style:not(.password-input)").first
        password_input = page.locator("input.password-input").first
        login_btn = page.locator("button.base-btn.type1").first

        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()
        expect(login_btn).to_be_visible()
        if sh: sh.capture(username_input, "verify_帳號欄位")
        if sh: sh.capture(password_input, "verify_密碼欄位")
        if sh: sh.capture(login_btn,      "verify_會員登入按鈕")

    def test_login_cta_navigates_to_login_page(self, page: Page, site_config):
        """TC-009：首頁 tap「個人」tab 可進入登入頁（未登入狀態）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)

        login.open_login_form()

        if sh: sh.full_page("verify_進入登入頁")
        expect(page).to_have_url(re.compile(r"/login"), timeout=8000)
        expect(page.locator("input.input-style:not(.password-input)").first).to_be_visible()

    def test_balance_visible(self, page: Page, site_config):
        """TC-010：登入後 navbar 直接顯示帳號 pill 與信用額度（無需開 panel）"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        sh = get_screenshotter(page)

        # navbar 帳號 pill
        expect(home.navbar_login_pill).to_have_text(site_config.username, timeout=10000)
        if sh: sh.capture(home.navbar_login_pill, f"verify_navbar_帳號顯示_{site_config.username}")

        # navbar 信用額度（非空）
        expect(home.navbar_balance).to_be_visible(timeout=5000)
        balance_text = (home.navbar_balance.text_content() or "").strip()
        if sh: sh.capture(home.navbar_balance, f"verify_navbar_信用額度非空_{balance_text}")
        assert balance_text != "", "navbar 信用額度欄位不應為空"

    @pytest.mark.skip(reason="desktop 版首頁無公告跑馬燈（probe 2026-06-26 確認）；公告已改隸右側 sidebar（.sidebar-item.announce），改由 feature/sidebar 涵蓋。此 marquee 測試永久不適用。")
    def test_announcement_marquee(self, page: Page, site_config):
        """TC-011：[OBSOLETE] 首頁公告跑馬燈 — desktop 已移除，公告移入 sidebar（見 feature/sidebar）"""

    def test_hot_games_section(self, page: Page, site_config):
        """TC-012：首頁顯示 hero section 標題與遊戲卡片。

        2026-05-18 換版：舊 .game-slot / .section-title 已被新版 grid 卡片取代。
        改驗 hero section 的 span.category-title（來財獨家/爆分精選/活動專區）
        + 任一遊戲卡片（.grid > .relative.cursor-pointer，全站 82 張）。
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        sh = get_screenshotter(page)
        # hero section title anchor（locale-agnostic via .first）
        section_title = page.locator('span.category-title').first
        expect(section_title).to_be_visible(timeout=5000)
        if sh: sh.capture(section_title, "verify_hero_section_標題")

        # 遊戲卡片（至少一張可見）— grid 卡片是 cursor-pointer 的 .relative div
        game_card = page.locator('.grid > .relative.cursor-pointer').first
        game_card.scroll_into_view_if_needed()
        if sh: sh.capture(game_card, "verify_遊戲卡片")

    def test_casino_halls_visible(self, page: Page, site_config):
        """TC-013：首頁顯示真人廳館 section（casino_banner + 至少一張廳館卡片）。

        2026-05-18 換版：廳館卡片 alt 全為空字串，無法用 img[alt="T9真人"] 等斷言。
        產品變動：RC 真人廳館已下架，現存 T9 / DG / MT / AB（歐博）四廳。
        改驗 casino banner 可見 + section 內 ≥1 張卡片，避免硬寫廳數。
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        sh = get_screenshotter(page)

        # casino section banner（image src 包含 category_banner_casino 為 anchor）
        casino_banner = page.locator("img[src*='category_banner_casino']").first
        casino_banner.scroll_into_view_if_needed()
        if sh: sh.capture(casino_banner, "verify_真人廳館_banner")
        expect(casino_banner).to_be_visible(timeout=5000)

        # section 內至少一張廳館卡片可見（含 T9/DG/MT/AB；RC 已下架）
        casino_cards = (
            page.locator("img[src*='category_banner_casino']")
            .locator("xpath=../..")
            .locator(".relative.cursor-pointer")
        )
        if sh: sh.full_page("verify_真人廳館_section_整體")
        assert casino_cards.count() >= 1, "真人廳館 section 應至少有 1 張卡片"

    def test_member_center_opens(self, page: Page, site_config):
        """TC-014：tap 底部「個人」tab 開啟 .dialog-mask-full overlay panel 並顯示帳號。

        2026-05-18 換版：個人中心改為 SPA inline panel，URL 維持 /。
        不再斷言 URL 變化，改驗 panel visible + 登出按鈕可見。
        """
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_member_center()
        if sh: sh.full_page("verify_member_center_panel開啟")

        # panel 已開
        expect(home.member_panel).to_be_visible(timeout=5000)

        # 登出按鈕可見代表 panel 已載入
        if sh: sh.capture(home.logout_btn, "verify_登出按鈕可見")
        expect(home.logout_btn).to_be_visible(timeout=5000)


# ─────────────────────────────────────────────────────────────
# 導覽列分類切換（2026-05-18 換版後 .cat-btn 已不存在）
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.lt
class TestNavigation:
    """TC-015：原 `.cat-btn` 分類 tab 在 2026-05-18 換版已被 swipe sections 取代，
    `.cat-btn--selected` 切換機制不存在。整組 skip 待產品決定新版分類互動模式後重寫。
    """

    @pytest.mark.skip(reason="desktop 版分類 tab 切換機制（.cat-btn--selected）已由產品移除（probe 2026-06-26 確認），改為單頁 3 個 swipe sections（span.category-title：來財獨家/爆分精選/活動專區），無 tab 切換互動。section 存在性已由 TestHome::test_hot_games_section 涵蓋。此測試永久不適用。")
    @pytest.mark.parametrize("nav_item", [
        "我的最愛",
        "台灣真人",
        "國際真人",
        "更多",
    ])
    def test_nav_cat_btn_switches_selected(self, page: Page, site_config, nav_item):
        """TC-015：tap `.cat-btn` 後該項目有 `.cat-btn--selected` class（已過時）"""
