"""
視覺健康度驗證（DOM metrics，非截圖比對）
WIN-VIS-001~007

2026-05-18 換版要點：
- 原 `.cat-btn` / `.shadow-menubar` 已消失（換為 swipe sections + `.footer-bg`）
- /login 元素 class 換掉（`input.login-input` → `input.input-style/.password-input`、
  `button.btn-login/.btn-browse` → `button.base-btn.type1/.type2`）
- navbar `.bg-navbar` → `.nav-bg-m`
- 原 xfail(strict=True) 守門（i18n hydration 衍生 visual 問題）已解除，產品端已修復
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter
from tests.lt.feature.visual.helpers import BANNER_SELECTORS


LoginPage = get_login_page_class("lt")


@pytest.mark.p2
@pytest.mark.lt
@pytest.mark.visual
class TestVisual:
    """WIN-VIS-001~007：視覺健康度驗證（版面、破圖、對齊）"""

    def test_home_no_horizontal_overflow(self, page: Page, site_config):
        """WIN-VIS-001：首頁沒有明顯橫向超框（scrollWidth <= innerWidth + 4）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        if sh: sh.full_page(f"verify_首頁橫向超框檢測_sw{metrics['scrollWidth']}_iw{metrics['innerWidth']}")
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"

    def test_home_no_broken_images(self, page: Page, site_config):
        """WIN-VIS-002：首頁圖片資源沒有明顯破圖"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        # 排除 src='' 空圖：那是「中央 footer tab 缺 icon」站點 bug（empty-src），
        # 由 test_i18n_hydration::test_home_images_no_empty_src（xfail strict）專責守門。
        # 本測試專注抓「真·載入失敗」的圖（有 src 但 naturalWidth 0），仍能抓出 NEW 破圖。
        broken = page.locator("img").evaluate_all("""imgs =>
            imgs
                .map(img => ({ src: img.getAttribute('src'), complete: img.complete, naturalWidth: img.naturalWidth }))
                .filter(img => img.complete && img.naturalWidth === 0 && img.src && img.src !== '')
        """)
        total_imgs = page.locator("img").count()
        # 截圖先於 assert
        if sh: sh.full_page(f"verify_首頁破圖檢測_total{total_imgs}_broken{len(broken)}")
        assert broken == [], f"發現破圖：{broken}"

    def test_home_banner_visible(self, page: Page, site_config):
        """WIN-VIS-003：首頁主視覺輪播 banner 可見

        2026-05-18 換版：舊 `.slider-box` 不再存在。新版 hero section 用多個 swiper
        承載主視覺；改驗第一個 `.swiper` 在 viewport 內。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        banner = page.locator('.swiper').first
        banner.scroll_into_view_if_needed()
        sh = get_screenshotter(page)
        if sh: sh.capture(banner, "verify_banner區塊可見檢測")
        expect(banner).to_be_visible(timeout=8000)

    def test_home_text_not_clipped(self, page: Page, site_config):
        """WIN-VIS-004：首頁主要文案區塊未明顯被裁切（允許 ellipsis 設計，排除 overflow:hidden 節點）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        overflow_nodes = page.evaluate("""() => {
            const targets = Array.from(document.querySelectorAll('a, button, p, span, h1, h2, h3'));
            return targets
                .map(el => {
                    const style = window.getComputedStyle(el);
                    return {
                        text: (el.textContent || '').trim().slice(0, 40),
                        clientWidth: el.clientWidth,
                        scrollWidth: el.scrollWidth,
                        overflowX: style.overflowX,
                        textOverflow: style.textOverflow,
                    };
                })
                .filter(item => item.text && item.clientWidth > 0 && item.scrollWidth - item.clientWidth > 20)
                .filter(item => item.overflowX !== 'hidden' && item.textOverflow !== 'ellipsis')
                .slice(0, 10);
        }""")
        if sh: sh.full_page(f"verify_首頁文案超框檢測_overflow{len(overflow_nodes)}")
        assert overflow_nodes == [], f"發現未設裁切控制卻溢出的文案節點：{overflow_nodes}"

    def test_login_page_no_horizontal_overflow(self, page: Page, site_config):
        """WIN-VIS-005：登入頁沒有明顯橫向超框"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        if sh: sh.full_page(f"verify_登入頁橫向超框檢測_sw{metrics['scrollWidth']}_iw{metrics['innerWidth']}")
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"登入頁橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"

    def test_login_form_alignment(self, page: Page, site_config):
        """WIN-VIS-006：登入表單對齊 — inputs 與 buttons 分群對齊。

        2026-05-18 換版：用 POM 新版 selector（input.input-style / .password-input、
        button.base-btn.type1 / .type2），不再寫死舊 `login-input` / `btn-login` 等 class。
        """
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)

        for loc, label in [
            (login.username_input, "verify_login_username_input對齊"),
            (login.password_input, "verify_login_password_input對齊"),
            (login.login_btn,      "verify_login_登入按鈕對齊"),
            (login.browse_btn,     "verify_login_先去逛逛按鈕對齊"),
        ]:
            loc.scroll_into_view_if_needed()
            if sh: sh.capture(loc, label)

        metrics = page.evaluate("""() => {
            const rect = el => {
                const box = el.getBoundingClientRect();
                return { x: box.x, width: box.width };
            };
            const username  = document.querySelector('input.input-style:not(.password-input)');
            const password  = document.querySelector('input.password-input');
            const loginBtn  = document.querySelector('button.base-btn.type1');
            const browseBtn = document.querySelector('button.base-btn.type2');
            return {
                username:  rect(username),
                password:  rect(password),
                loginBtn:  rect(loginBtn),
                browseBtn: rect(browseBtn),
            };
        }""")
        input_xs     = [metrics["username"]["x"],     metrics["password"]["x"]]
        input_widths = [metrics["username"]["width"], metrics["password"]["width"]]
        btn_xs       = [metrics["loginBtn"]["x"],     metrics["browseBtn"]["x"]]
        btn_widths   = [metrics["loginBtn"]["width"], metrics["browseBtn"]["width"]]
        padding      = metrics["username"]["x"] - metrics["loginBtn"]["x"]

        if sh: sh.full_page(f"verify_login表單整體對齊檢測_padding{padding}px")

        # inputs 之間：左邊界嚴格對齊；寬度允許 ≤ 30px 差異（password 右側 toggle 眼睛 icon 擠壓視覺寬度）
        assert max(input_xs)     - min(input_xs)     <= 2,  f"inputs 左邊界未對齊：{metrics}"
        assert max(input_widths) - min(input_widths) <= 30, f"inputs 寬度差異超過 icon 擠壓容忍（30px）：{metrics}"

        # buttons 之間嚴格對齊
        assert max(btn_xs)     - min(btn_xs)     <= 2, f"buttons 左邊界未對齊：{metrics}"
        assert max(btn_widths) - min(btn_widths) <= 2, f"buttons 寬度未一致：{metrics}"

        # inputs 左邊界相對 buttons 的 padding 落在合理範圍（desktop responsive 寬鬆些）
        assert abs(padding) <= 40, f"inputs/buttons 左邊界差距超過合理 padding：{padding}px"

    @pytest.mark.skip(reason="DEFER：desktop 版首頁為長捲動單頁（hero swipe sections + .footer-bg 5 tab），舊 .cat-btn/.shadow-menubar viewport 驗證不適用。新版 viewport 驗證低優先；且底部中央 footer tab 有站點 bug（破 icon，見 docs/product-bugs-to-report.md），待產品修後再設計。")
    def test_home_navbar_and_login_in_viewport(self, page: Page, site_config):
        """WIN-VIS-007：[DEFER] 首頁可點擊元素在視窗內 — 待新版 viewport 驗證設計 + footer tab 站點 bug 修復"""
