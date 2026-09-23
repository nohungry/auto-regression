"""
WIN-I18N-HYDR-001~003：i18n 與資源 hydrate 健康度守門（desktop 版，2026-05-18 rewrite）

守門「預設語系下首頁載入時是否完整 hydrate」：
- 首頁區塊標題（`.group > p.tip-single.whitespace-nowrap`）不應出現 raw i18n key（`front.xxx.yyy` 格式）
- 側欄入口（`.sidebar-item`，取代已移除的底部 footer tab）不應出現 raw i18n key
- 首頁可見 `<img>` 不應存在 `src=""` 空值

**狀態（2026-09-23 probe）**：3 個 test 皆為 enforce 模式（無 xfail 守門），regression 再現直接 FAIL。
沿革：dev-lt 2026-04-23 hydration regression 修復後首次解除 xfail（PR #49）；
破圖那條曾因產品 bug #1（底部中央 footer tab 圖示 src 空）再度掛上 xfail(strict)（PR #121），
第三次換版移除整個 footer 後該實例消失、XPASS 觸發提醒，2026-09-23 再次解除轉 enforce。
參考舊版 selector：原 `.cat-btn` 與 `.shadow-menubar` 在 2026-05-18 換版後均不存在。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lt")

# Raw i18n key 格式：前綴小寫、後續以 . 分隔任意識別字（支援 camelCase 與 _）
# 實例：front.category_icons.lobby / front.Footer.Tab.member_center
RAW_I18N_KEY_REGEX = r"^[a-z]+\.[a-zA-Z_.]+$"


@pytest.mark.p2
@pytest.mark.lt
@pytest.mark.i18n
class TestI18NHydration:
    """WIN-I18N-HYDR-001~003：i18n 與資源 hydrate 健康度"""

    def test_home_category_title_no_raw_i18n_key(self, page: Page, site_config):
        """WIN-I18N-HYDR-001：首頁區塊標題不應為 raw i18n key

        2026-09-23 修正假綠燈：舊 `span.category-title` 在第三次換版後已不存在，
        `querySelectorAll` 回空陣列 → `raw_keys == []` 恆真，測試看似通過卻什麼都沒驗。
        改用新版區塊標題 `.group > p.tip-single.whitespace-nowrap`，並加 **count 守衛**：
        命中 0 個元素直接判失敗，避免 selector 再漂移時又無聲退化成空集合恆真。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        result = page.evaluate(
            """(pattern) => {
                const regex = new RegExp(pattern);
                const texts = [...document.querySelectorAll('.group > p.tip-single.whitespace-nowrap')]
                    .map(el => (el.textContent || '').trim());
                return { total: texts.length, rawKeys: texts.filter(t => regex.test(t)) };
            }""",
            RAW_I18N_KEY_REGEX,
        )
        raw_keys = result["rawKeys"]
        if sh: sh.full_page(
            f"verify_區塊標題i18n_hydrate現況_total{result['total']}_raw{len(raw_keys)}"
        )
        assert result["total"] > 0, "首頁區塊標題命中 0 個元素：selector 已漂移，此測試失去守門意義"
        assert raw_keys == [], f"首頁區塊標題出現 raw i18n key（hydrate 失敗）：{raw_keys}"

    def test_sidebar_entry_no_raw_i18n_key(self, page: Page, site_config):
        """WIN-I18N-HYDR-002：側欄入口文案不應為 raw i18n key

        2026-09-23 修正假綠燈：底部 footer 在第三次換版被整個移除，`.footer-bg .content`
        命中 0 → 斷言恆真。footer 原本承載的入口（公告 / 排行榜 / 個人）已改隸右側側欄，
        故本條改守側欄 7 個 `.sidebar-item`（個人資訊 / 遊戲明細 / 精彩瞬間 / 站內信 /
        來財公告 / 排行榜 / 固定維護時間），同樣加 count 守衛。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        result = page.evaluate(
            """(pattern) => {
                const regex = new RegExp(pattern);
                const texts = [...document.querySelectorAll('.sidebar-item')]
                    .map(el => (el.textContent || '').trim());
                return { total: texts.length, rawKeys: texts.filter(t => regex.test(t)) };
            }""",
            RAW_I18N_KEY_REGEX,
        )
        raw_keys = result["rawKeys"]
        if sh: sh.full_page(
            f"verify_側欄入口i18n_hydrate現況_total{result['total']}_raw{len(raw_keys)}"
        )
        assert result["total"] > 0, "側欄入口命中 0 個元素：selector 已漂移，此測試失去守門意義"
        assert raw_keys == [], f"側欄入口出現 raw i18n key（hydrate 失敗）：{raw_keys}"

    def test_home_images_no_empty_src(self, page: Page, site_config):
        """WIN-I18N-HYDR-003：首頁可見 `<img>` 不應存在 `src=""` 空值（通用破圖守門）。

        2026-09-23 解除 xfail：原本以 xfail(strict) 守產品 bug #1（首頁底部中央 footer tab
        圖示 src 永久空）。第三次換版把整個底部 footer 移除，該破圖實例隨之消失，
        實機複驗首頁 empty src img = 0 → strict xfail 觸發 XPASS 提醒解除。
        本測試並非為 footer 而寫（footer 只是當時唯一觸發實例），通用破圖守門價值仍在，
        故照 PR #49 前例改為 enforce：日後再出現破圖會直接 FAIL。
        """
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
