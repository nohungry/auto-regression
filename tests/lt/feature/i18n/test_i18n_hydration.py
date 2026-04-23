"""
WIN-I18N-HYDR-001~003：i18n 與資源 hydrate 健康度守門

與既有 locale 切換驗證不同，本檔守門「預設語系下首頁載入時是否完整 hydrate」：
- 首頁 `.cat-btn` 與底部 tabbar 文案不應出現 raw i18n key（`front.xxx.yyy` 格式）
- 首頁可見 `<img>` 不應存在 `src=""` 空值

**現況（2026-04-23）**：dev-lt 產品端 regression 造成 i18n 部分 key 未 hydrate +
遊戲 icon CDN 回傳空 URL，本檔 3 個測試以 `xfail(strict=True)` 標記。
當產品端修復後會觸發 XPASS 強制提醒 un-xfail（守門機制）。

參考：
- PR #16 `TestI18NLangSwitcher.test_lang_text_reflects_locale` 同樣採 xfail(strict=True) pattern
- `feedback_regression_notify_before_fix.md` — 產品端 regression 已通知主管
"""

import re
import pytest
from playwright.sync_api import Page
from pages.lt.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter

# Raw i18n key 格式：前綴小寫、後續以 . 分隔任意識別字（支援 camelCase 與 _）
# 實例：front.category_icons.lobby / front.Footer.Tab.member_center
RAW_I18N_KEY_REGEX = r"^[a-z]+\.[a-zA-Z_.]+$"


@pytest.mark.p2
@pytest.mark.lt
@pytest.mark.i18n
class TestI18NHydration:
    """WIN-I18N-HYDR-001~003：i18n 與資源 hydrate 健康度"""

    @pytest.mark.xfail(
        strict=True,
        reason="dev-lt 2026-04-23 regression: `.cat-btn` 出現 front.category_icons.* raw key 未 hydrate。"
               "產品端修復後觸發 XPASS → 移除此 xfail。",
    )
    def test_home_cat_btn_no_raw_i18n_key(self, page: Page, site_config):
        """WIN-I18N-HYDR-001：首頁 `.cat-btn` 文案不應為 raw i18n key"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        raw_keys = page.evaluate(
            """(pattern) => {
                const regex = new RegExp(pattern);
                return [...document.querySelectorAll('.cat-btn')]
                    .map(el => (el.textContent || '').trim())
                    .filter(text => regex.test(text));
            }""",
            RAW_I18N_KEY_REGEX,
        )
        if sh: sh.full_page(f"verify_cat_btn_i18n_hydrate現況_raw{len(raw_keys)}")
        assert raw_keys == [], f".cat-btn 出現 raw i18n key（hydrate 失敗）：{raw_keys}"

    @pytest.mark.xfail(
        strict=True,
        reason="dev-lt 2026-04-23 regression: 底部 tabbar 出現 front.Footer.Tab.* raw key 未 hydrate。"
               "產品端修復後觸發 XPASS → 移除此 xfail。",
    )
    def test_home_tabbar_no_raw_i18n_key(self, page: Page, site_config):
        """WIN-I18N-HYDR-002：底部 tabbar 文案不應為 raw i18n key"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        raw_keys = page.evaluate(
            """(pattern) => {
                const regex = new RegExp(pattern);
                return [...document.querySelectorAll('.shadow-menubar .cursor-pointer')]
                    .map(el => (el.textContent || '').trim())
                    .filter(text => regex.test(text));
            }""",
            RAW_I18N_KEY_REGEX,
        )
        if sh: sh.full_page(f"verify_tabbar_i18n_hydrate現況_raw{len(raw_keys)}")
        assert raw_keys == [], f"底部 tabbar 出現 raw i18n key（hydrate 失敗）：{raw_keys}"

    @pytest.mark.xfail(
        strict=True,
        reason='dev-lt 2026-04-23 regression: 遊戲 icon <img src=""> 空字串。'
               "產品端修復後觸發 XPASS → 移除此 xfail。",
    )
    def test_home_images_no_empty_src(self, page: Page, site_config):
        """WIN-I18N-HYDR-003：首頁可見 `<img>` 不應存在 `src=\"\"` 空值（動態值斷言：只驗非空）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        empty_src_imgs = page.evaluate(
            """() =>
                [...document.querySelectorAll('img')]
                    .filter(img => img.offsetWidth > 0 && (!img.getAttribute('src') || img.getAttribute('src') === ''))
                    .map(img => ({ alt: img.getAttribute('alt'), outer: img.outerHTML.slice(0, 120) }))
            """
        )
        if sh: sh.full_page(f"verify_img_src非空現況_empty{len(empty_src_imgs)}")
        assert empty_src_imgs == [], f'可見 <img> 存在 src="" 空字串：{empty_src_imgs}'
