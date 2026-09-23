"""
LT 文案一致性驗證（職責：預設語系繁中的品牌/結構文案）
WIN-COPY-001~005

2026-05-18 desktop 改版後重寫（probe 2026-06-26 確認）：
desktop 版精簡了登入/首頁，下列元素**產品端已移除**，對應測試改為 skip（永久不適用）：
- 首頁頁尾版權文案（無 Copyright 節點）
- 登入頁欄位標籤「會員帳號/登入密碼」（改為圖片化 header「登入帳號」，DOM 無文字）
- 登入頁免責聲明
- 首頁頁尾版權 / 登入頁欄位標籤 / 登入頁免責聲明（皆 probe 確認 DOM 無節點）

2026-09-23 複驗：`a[href^="/Categories/"]` 分類 nav 在第三次換版後**重新出現於 navbar**，
原「永久不適用」的 skip 已失效，`test_home_category_order` 改以 href 順序 enforce。

仍有效並重寫：首頁 title、登入頁送出鈕文案、密碼 placeholder（2026-09-23 對齊第三次換版：
送出鈕「會員登入」→「登入」、密碼 placeholder 規則句 →「密碼」、「先去逛逛」按鈕已移除）。
🚩 登入欄位未提示帳號長度規則（4-10）→ xfail(strict) 守門，產品補上後 XPASS。

多語系切換文案見 `tests/lt/feature/i18n/`（職責互補，本檔守繁中文案）。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lt")

# 首頁 navbar 分類入口順序（probe 2026-09-23）。
# 以 href 比對而非文案：LT 為五語系站，顯示文字會隨 locale 變動。
_EXPECTED_NAV_ROUTES = [
    "/",
    "/Categories/casino",
    "/Categories/slots",
    "/Categories/sports",
    "/Categories/lottery",
    "/Categories/fishing",
    "/Categories/mini-game",
]


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
        """WIN-COPY-002：登入頁送出鈕文案正確（登入）。

        2026-09-23 對齊第三次換版（probe 確認）：
        - 送出鈕文案「會員登入」→「登入」
        - 「先去逛逛」按鈕已被產品移除（POM `browse_btn` 同步刪除），該行斷言一併移除；
          從登入頁回首頁的路徑改由 `feature/public::test_leave_login_page_returns_home`
          驗 `img[alt="Exit"]` 涵蓋
        用 POM 結構性 selector（`button.primary-btn`，locale-agnostic）+ 繁中文案斷言。
        """
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)
        if sh: sh.capture(login.login_btn, "verify_登入CTA")
        expect(login.login_btn).to_have_text("登入", timeout=8000)

    def test_login_password_placeholder(self, page: Page, site_config):
        """WIN-COPY-003：登入頁密碼欄 placeholder 文案正確（密碼）。

        2026-09-23 對齊第三次換版：placeholder 由規則句「請填寫8-20位的字母或數字」
        改為純名詞「密碼」。舊文案同時也是產品 bug #2 的證據（帳號欄誤用密碼規則），
        換版後該症狀消失，但**兩欄都不再提示長度規則** —— 該訴求改由
        `test_login_username_placeholder` 的 xfail(strict) 繼續守門。
        """
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)
        if sh: sh.capture(login.password_input, "verify_密碼placeholder")
        expect(login.password_input).to_have_attribute("placeholder", "密碼")

    @pytest.mark.xfail(
        strict=True,
        reason="🚩 產品 copy 缺口：登入欄位未提示帳號長度規則（4-10 位）。"
               "原症狀為帳號欄誤用密碼規則 8-20（複製錯誤）；2026-09-23 換版後兩欄改為純名詞"
               "「用戶名」/「密碼」，複製錯誤消失但規則提示一併不見，訴求未被滿足故維持守門。"
               "產品補上規則提示後本測試 XPASS，屆時拿掉 xfail。見 docs/product-bugs-to-report.md #2。",
    )
    def test_login_username_placeholder(self, page: Page, site_config):
        """WIN-COPY-004：登入頁帳號欄 placeholder 應反映帳號規則（4-10 位）。"""
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

    def test_home_category_order(self, page: Page, site_config):
        """WIN-COPY-005d：首頁 navbar 分類入口順序符合預期。

        2026-09-23 un-skip：舊 skip 理由（desktop 版已移除分類 nav）在第三次換版後失效，
        `ul.nav-item` 重新提供 7 個分類入口。以 href 全等比對（含順序），不綁文案；
        href 帶 `#gameListSection` anchor，比對前去掉。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)

        nav = page.locator("ul.nav-item").first
        nav.wait_for(state="visible", timeout=15000)
        hrefs = [
            (h or "").split("#")[0]
            for h in page.locator("ul.nav-item a").evaluate_all(
                "els => els.map(e => e.getAttribute('href'))"
            )
        ]
        if sh: sh.capture(nav, f"verify_導覽列分類順序_count{len(hrefs)}")
        assert hrefs == _EXPECTED_NAV_ROUTES, (
            f"首頁導覽列分類入口順序與預期不符\n預期：{_EXPECTED_NAV_ROUTES}\n實際：{hrefs}"
        )
