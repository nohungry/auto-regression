"""
文案一致性驗證
WIN-COPY-001~005
"""

import pytest
from playwright.sync_api import Page, expect
from pages.dlt.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.copy
class TestCopy:
    """WIN-COPY-001~005：文案一致性驗證"""

    def test_home_title_and_footer(self, page: Page, site_config):
        """WIN-COPY-001：首頁標題與頁尾版權文案一致"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        expect(page).to_have_title("LM來財信用網")
        copyright_el = page.get_by_text("Copyright © 2025 LaiCai All rights reserved.").first
        expect(copyright_el).to_be_visible()
        if sh: sh.capture(copyright_el, "verify_版權文案")

    def test_login_page_placeholder_and_cta(self, page: Page, site_config):
        """WIN-COPY-002：登入頁 placeholder 與 CTA 文案正確"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)

        username_input = page.get_by_placeholder("請填寫4-10位的字母或數字")
        password_input = page.get_by_placeholder("請填寫 8-20 位的字母或數字")

        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()
        expect(page.get_by_role("button", name="登入")).to_contain_text("登入")
        expect(page.get_by_role("button", name="先去逛逛")).to_contain_text("先去逛逛")
        if sh: sh.capture(username_input, "verify_帳號placeholder")
        if sh: sh.capture(password_input, "verify_密碼placeholder")

    def test_login_page_field_labels(self, page: Page, site_config):
        """WIN-COPY-003：登入頁欄位標籤文案正確（會員登入/會員帳號/登入密碼）"""
        login = LoginPage(page, site_config.url)
        login.goto_login()

        body = page.locator("body")
        for text in ["會員登入", "會員帳號", "登入密碼"]:
            expect(body).to_contain_text(text)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_登入頁欄位標籤")

    def test_login_page_disclaimer(self, page: Page, site_config):
        """WIN-COPY-004：登入頁免責聲明文案存在"""
        login = LoginPage(page, site_config.url)
        login.goto_login()

        body = page.locator("body")
        expect(body).to_contain_text("登入即表示您已閱讀並同意本平台之")
        expect(body).to_contain_text("免責聲明")
        expect(body).to_contain_text("如不同意請勿使用本服務")
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_免責聲明文案")

    def test_home_category_order(self, page: Page, site_config):
        """WIN-COPY-005：首頁四個主分類文案順序一致（熱門/真人/電子/捕魚）"""
        login = LoginPage(page, site_config.url)
        login.goto()

        nav_texts = page.locator('a[href^="/Categories/"]').evaluate_all(
            """links => links
                .map(link => (link.textContent || '').trim())
                .filter(Boolean)
                .slice(0, 4)"""
        )
        assert nav_texts == ["熱門", "真人", "電子", "捕魚"], \
            f"分類順序不符，實際：{nav_texts}"
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_分類文案順序")
