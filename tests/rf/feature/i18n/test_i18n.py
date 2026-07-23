"""
RF i18n 輕量驗證（金爺娛樂城）
RF-I18N-001 ~ 003

範圍：
- RF-I18N-001：語言切換器存在且可見（.lang-selector，常駐 globe icon）
- RF-I18N-002：預設語系 cookie i18n_locale=tw 已設定（Nuxt i18n 模組啟用）
- RF-I18N-003：切換 English 後 nav 文案改為英文、cookie 更新為 en

probe 2026-06-17：
- RF 有 .lang-selector（globe icon，w=48 h=28，常駐可見於 header 右側）
- 5 語系：繁體中文 / 简体中文 / English / Tiếng Việt / ภาษาไทย
- 預設語系：繁體中文（i18n_locale=tw）
- 切換後：nav a/button 文案即時更新（首頁→Home、真人→Live Casino 等）
- .lang-selector__list li 的 inner_text() 在 headless 模式下回空字串；
  Switch 操作改為以 nth() 定位（English 為第三個 li，index=2）
- Login 頁（/Login）無語言切換器（i18n 僅首頁 / 已登入頁可用）
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter

HomePage = get_home_page_class("rf")

# 繁體中文預設 nav 文案（未登入首頁）
EXPECTED_NAV_TW = ["首頁", "真人", "電子", "捕魚"]

# English nav 文案（切換後）
EXPECTED_NAV_EN = ["Home", "Live Casino", "Slots", "Fishing"]


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.i18n
class TestI18n:
    """RF-I18N-001 ~ 003：語言切換器存在性 + cookie + 切換效果"""

    def test_language_selector_present(self, page: Page, site_config):
        """RF-I18N-001：.lang-selector（globe icon）常駐可見於 header

        probe 2026-06-17：.lang-selector w=48, h=28，位於右上角（x=1572, y=47），
        為常駐可見的 globe icon 按鈕，非 hover 式 tooltip。
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        lang_sel = page.locator(".lang-selector")
        expect(lang_sel).to_be_visible(timeout=15000)
        lang_sel.scroll_into_view_if_needed()
        sh = get_screenshotter(page)
        if sh:
            sh.capture(lang_sel, "verify_語言切換器globe_icon存在可見")

    def test_default_lang_cookie(self, page: Page, site_config):
        """RF-I18N-002：預設語系 cookie i18n_locale=tw 已設定

        斷言策略：
        - 只驗 cookie 存在且值為 'tw'（繁體中文預設語系）
        - RF 使用 i18n_locale（非 i18n_redirected），為 RF 站台特有 cookie 名
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)
        if sh:
            sh.full_page("verify_i18n_locale_cookie_預設tw")
        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        assert "i18n_locale" in cookies, (
            f"預期 i18n_locale cookie 存在，實際 cookies 名稱={list(cookies.keys())}"
        )
        assert cookies["i18n_locale"] == "tw", (
            f"預期 i18n_locale=tw（繁體中文），實際={cookies['i18n_locale']}"
        )

    def test_switch_to_english(self, page: Page, site_config):
        """RF-I18N-003：切換 English 後 nav 文案改為英文、cookie 更新為 en

        斷言策略：
        - 切換後 nav.menu_nav 的 a/button 文案列表 == EXPECTED_NAV_EN
        - cookie i18n_locale 更新為 'en'
        - 不驗整站所有文案，只驗 nav（穩定錨點）

        定位策略：透過 POM switch_language("English")，內部以 filter(has_text="English")
        定位（順序無關，避免後端調整語系排序時靜默命中錯項）。實機確認 headless 下
        .lang-selector__list li 展開後文字存在、filter(has_text) 命中唯一（count=1）。
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        home = HomePage(page)
        sh = get_screenshotter(page)

        # 展開語言選單 → 以文字定位點 English（走 POM，filter(has_text) 順序無關）
        home.open_lang_selector()
        home.switch_language("English")

        # 截圖後再斷言
        nav = page.locator("nav.menu_nav")
        if sh:
            sh.capture(nav, "verify_nav文案切換English後")

        actual_nav = page.evaluate("""
        () => Array.from(document.querySelectorAll('nav.menu_nav a, nav.menu_nav button'))
            .map(e => (e.textContent||'').trim()).filter(t => t)
        """)
        assert actual_nav == EXPECTED_NAV_EN, (
            f"切換 English 後 nav 文案不符，預期={EXPECTED_NAV_EN}，實際={actual_nav}"
        )

        # 驗 cookie
        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        if sh:
            sh.full_page(f"verify_i18n_locale_cookie_切換後_{cookies.get('i18n_locale', 'not_found')}")
        assert cookies.get("i18n_locale") == "en", (
            f"切換 English 後預期 i18n_locale=en，實際={cookies.get('i18n_locale')}"
        )

    def test_switch_back_to_chinese(self, page: Page, site_config):
        """RF-I18N-004：英↔繁雙向切換，切回繁體中文後 nav 文案與 cookie 恢復

        延伸 test_switch_to_english（單向）→ 補雙向恢復（en→tw）：
        - 先切 English：cookie i18n_locale=en
        - 再切回繁體中文：nav.menu_nav 文案 == EXPECTED_NAV_TW、cookie i18n_locale=tw
        斷言策略：驗語言狀態可還原（非僅驗預設值）；nav 為穩定錨點，不驗整站文案。
        定位沿用 POM switch_language（filter(has_text)，順序無關；headless 下 inner_text 空
        但 has_text 過濾可命中）；每次切換前重新 open_lang_selector（切換後選單會收合）。
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        home = HomePage(page)
        sh = get_screenshotter(page)

        # → English
        home.open_lang_selector()
        home.switch_language("English")
        cookies_en = {c["name"]: c["value"] for c in page.context.cookies()}
        if sh:
            sh.full_page(f"verify_i18n_locale_cookie_切換English後_{cookies_en.get('i18n_locale', 'not_found')}")
        assert cookies_en.get("i18n_locale") == "en", (
            f"切換 English 後預期 i18n_locale=en，實際={cookies_en.get('i18n_locale')}"
        )

        # → 繁體中文（雙向恢復）
        home.open_lang_selector()
        home.switch_language("繁體中文")

        nav = page.locator("nav.menu_nav")
        if sh:
            sh.capture(nav, "verify_nav文案切回繁體中文")
        actual_nav = page.evaluate("""
        () => Array.from(document.querySelectorAll('nav.menu_nav a, nav.menu_nav button'))
            .map(e => (e.textContent||'').trim()).filter(t => t)
        """)
        assert actual_nav == EXPECTED_NAV_TW, (
            f"切回繁體中文後 nav 文案不符，預期={EXPECTED_NAV_TW}，實際={actual_nav}"
        )

        cookies_tw = {c["name"]: c["value"] for c in page.context.cookies()}
        if sh:
            sh.full_page(f"verify_i18n_locale_cookie_切回繁中後_{cookies_tw.get('i18n_locale', 'not_found')}")
        assert cookies_tw.get("i18n_locale") == "tw", (
            f"切回繁體中文後預期 i18n_locale=tw，實際={cookies_tw.get('i18n_locale')}"
        )

    def test_switch_to_simplified_cookie(self, page: Page, site_config):
        """RF-I18N-005：切換简体中文後 i18n_locale cookie 更新為 cn

        對應 test_switch_to_english 的「cookie 值對應變化」概念，走非英文路徑（cn）。
        斷言策略：只驗 cookie i18n_locale=cn（POM switch_language docstring 記載 tw/cn/en/vi/th
        對應各語系）；不斷言 nav 文案（本檔未有確認的简体 nav 對照，依「不確定不寫」原則略過）。
        定位沿用 POM switch_language（filter(has_text="简体中文")）。
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_lang_selector()
        home.switch_language("简体中文")

        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        if sh:
            sh.full_page(f"verify_i18n_locale_cookie_切換简体后_{cookies.get('i18n_locale', 'not_found')}")
        assert cookies.get("i18n_locale") == "cn", (
            f"切換 简体中文 後預期 i18n_locale=cn，實際={cookies.get('i18n_locale')}"
        )
