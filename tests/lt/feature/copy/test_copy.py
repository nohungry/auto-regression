"""
LT 文案一致性驗證（職責：預設語系繁中的品牌/結構文案）
WIN-COPY-001~005

2026-05-18 desktop 改版後重寫（probe 2026-06-26 確認）：
desktop 版精簡了登入/首頁，下列元素**產品端已移除**，對應測試改為 skip（永久不適用）：
- 首頁頁尾版權文案（無 Copyright 節點）
- 登入頁欄位標籤「會員帳號/登入密碼」（改為圖片化 header「登入帳號」，DOM 無文字）
- 登入頁免責聲明
- 首頁 `a[href^="/Categories/"]` 分類 nav（改單頁 swipe sections，見 test_p0_smoke / test_hot_games_section）

仍有效並重寫：首頁 title、登入頁 CTA（會員登入/先去逛逛）、密碼 placeholder。
🚩 帳號欄 placeholder 疑似產品 bug（顯示 8-20，應為 4-10）→ xfail(strict) 守門，修正後 XPASS。

多語系切換文案見 `tests/lt/feature/i18n/`（職責互補，本檔守繁中文案）。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lt")


@pytest.mark.p2
@pytest.mark.lt
@pytest.mark.copy
class TestCopy:
    """WIN-COPY-001~005：文案一致性驗證（desktop 版）"""

    def test_home_title(self, page: Page, site_config):
        """WIN-COPY-001：首頁 <title> 文案一致（LM來財信用網）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        expect(page).to_have_title("LM來財信用網")
        if sh: sh.full_page("verify_首頁title")

    def test_login_cta_buttons(self, page: Page, site_config):
        """WIN-COPY-002：登入頁 CTA 文案正確（會員登入 / 先去逛逛）。
        用 POM 結構性 selector（type1/type2，locale-agnostic）+ 繁中文案斷言。
        """
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)
        expect(login.login_btn).to_have_text("會員登入", timeout=8000)
        expect(login.browse_btn).to_have_text("先去逛逛")
        if sh: sh.capture(login.login_btn, "verify_登入CTA")

    def test_login_password_placeholder(self, page: Page, site_config):
        """WIN-COPY-003：登入頁密碼欄 placeholder 文案正確（請填寫8-20位的字母或數字）"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)
        expect(login.password_input).to_have_attribute(
            "placeholder", "請填寫8-20位的字母或數字"
        )
        if sh: sh.capture(login.password_input, "verify_密碼placeholder")

    @pytest.mark.xfail(
        strict=True,
        reason="🚩 產品 copy bug：帳號欄 placeholder 顯示「請填寫8-20位的字母或數字」，"
               "應為帳號規則（4-10 位，同 password 8-20 疑為複製錯誤）。修正後本測試 XPASS。",
    )
    def test_login_username_placeholder(self, page: Page, site_config):
        """WIN-COPY-004：登入頁帳號欄 placeholder 應反映帳號規則（4-10 位），非密碼的 8-20。"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        ph = login.username_input.get_attribute("placeholder") or ""
        assert "4-10" in ph, f"帳號 placeholder 應含 4-10 帳號規則，實際：{ph!r}"

    @pytest.mark.skip(reason="desktop 版首頁已移除頁尾版權文案（probe 2026-06-26：DOM 無 Copyright/版權 節點）。永久不適用。")
    def test_home_footer_copyright(self, page: Page, site_config):
        """WIN-COPY-005a：[OBSOLETE] 首頁頁尾版權 — desktop 已移除"""

    @pytest.mark.skip(reason="desktop 版登入頁無欄位標籤文字「會員帳號/登入密碼」；header「登入帳號」為圖片（DOM 無文字）。永久不適用。")
    def test_login_field_labels(self, page: Page, site_config):
        """WIN-COPY-005b：[OBSOLETE] 登入頁欄位標籤 — desktop 改圖片化 header"""

    @pytest.mark.skip(reason="desktop 版登入頁已移除免責聲明文案（probe 2026-06-26）。永久不適用。")
    def test_login_disclaimer(self, page: Page, site_config):
        """WIN-COPY-005c：[OBSOLETE] 登入頁免責聲明 — desktop 已移除"""

    @pytest.mark.skip(reason="desktop 版首頁已移除 a[href^='/Categories/'] 分類 nav，改單頁 swipe sections（來財獨家/爆分精選/活動專區）。section 由 test_hot_games_section 涵蓋。永久不適用。")
    def test_home_category_order(self, page: Page, site_config):
        """WIN-COPY-005d：[OBSOLETE] 首頁分類順序 — desktop 改 swipe sections"""
