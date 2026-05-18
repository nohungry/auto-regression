"""
WIN-I18N-HYDR-001~003：i18n 與資源 hydrate 健康度守門（desktop 版，2026-05-18 rewrite）

守門「預設語系下首頁載入時是否完整 hydrate」：
- 首頁 hero section title（`span.category-title`）不應出現 raw i18n key（`front.xxx.yyy` 格式）
- 底部 footer tab（`.footer-bg .content`）不應出現 raw i18n key
- 首頁可見 `<img>` 不應存在 `src=""` 空值

**狀態（2026-05-18 probe）**：dev-lt 2026-04-23 regression 已修復（無 raw key、無 empty src img）；
原 xfail(strict=True) 守門已解除，3 個 test 改為 enforce 模式 — 若日後 regression 再現會直接 FAIL。
參考舊版 selector：原 `.cat-btn` 與 `.shadow-menubar` 在 2026-05-18 換版後均不存在。
"""

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

    def test_home_category_title_no_raw_i18n_key(self, page: Page, site_config):
        """WIN-I18N-HYDR-001：首頁 hero section title 不應為 raw i18n key

        2026-05-18 換版：原 `.cat-btn` 已被 `span.category-title` 取代。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        raw_keys = page.evaluate(
            """(pattern) => {
                const regex = new RegExp(pattern);
                return [...document.querySelectorAll('span.category-title')]
                    .map(el => (el.textContent || '').trim())
                    .filter(text => regex.test(text));
            }""",
            RAW_I18N_KEY_REGEX,
        )
        if sh: sh.full_page(f"verify_category_title_i18n_hydrate現況_raw{len(raw_keys)}")
        assert raw_keys == [], f"span.category-title 出現 raw i18n key（hydrate 失敗）：{raw_keys}"

    def test_home_footer_tab_no_raw_i18n_key(self, page: Page, site_config):
        """WIN-I18N-HYDR-002：底部 footer tab 文案不應為 raw i18n key

        2026-05-18 換版：原 `.shadow-menubar .cursor-pointer` 已被 `.footer-bg .content` 取代。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        raw_keys = page.evaluate(
            """(pattern) => {
                const regex = new RegExp(pattern);
                return [...document.querySelectorAll('.footer-bg .content')]
                    .map(el => (el.textContent || '').trim())
                    .filter(text => regex.test(text));
            }""",
            RAW_I18N_KEY_REGEX,
        )
        if sh: sh.full_page(f"verify_footer_tab_i18n_hydrate現況_raw{len(raw_keys)}")
        assert raw_keys == [], f"footer tab 出現 raw i18n key（hydrate 失敗）：{raw_keys}"

    def test_home_images_no_empty_src(self, page: Page, site_config):
        """WIN-I18N-HYDR-003：首頁可見 `<img>` 不應存在 `src=""` 空值（動態值斷言：只驗非空）"""
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
