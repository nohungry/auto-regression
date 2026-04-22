"""
視覺健康度驗證（DOM metrics，非截圖比對）
WIN-VIS-001~007
"""

import pytest
from playwright.sync_api import Page, expect
from pages.lt.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter
from tests.lt.feature.visual.helpers import BANNER_SELECTORS


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
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"
        if sh: sh.full_page(f"verify_首頁無橫向超框_sw{metrics['scrollWidth']}_iw{metrics['innerWidth']}")

    def test_home_no_broken_images(self, page: Page, site_config):
        """WIN-VIS-002：首頁圖片資源沒有明顯破圖"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        broken = page.locator("img").evaluate_all("""imgs =>
            imgs
                .map(img => ({ src: img.getAttribute('src'), complete: img.complete, naturalWidth: img.naturalWidth }))
                .filter(img => img.complete && img.naturalWidth === 0)
        """)
        total_imgs = page.locator("img").count()
        assert broken == [], f"發現破圖：{broken}"
        if sh: sh.full_page(f"verify_首頁圖片無破圖_total{total_imgs}")

    def test_home_banner_visible(self, page: Page, site_config):
        """WIN-VIS-003：首頁主視覺輪播 banner 可見（WAP `.slider-box` 在 viewport 內）

        舊 selector `img[src*="Page/Pc"] / MainPageImage / [class*="banner"] img` 為桌機時代殘留，
        WAP 下會誤中頁尾 blockchain 宣傳區（y~2100px，在 viewport 外），雖然斷言過但紅框截圖看不見。
        WAP 首頁主 banner 為 `.slider-box` 輪播容器（y=135, w=390x219）。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        banner = page.locator('.slider-box').first
        expect(banner).to_be_visible(timeout=8000)
        banner.scroll_into_view_if_needed()
        sh = get_screenshotter(page)
        if sh: sh.capture(banner, "verify_banner區塊可見")

    def test_home_text_not_clipped(self, page: Page, site_config):
        """WIN-VIS-004：首頁主要文案區塊未明顯被裁切（允許 ellipsis 設計，排除 overflow:hidden 節點）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)

        # WAP 部分文案（如「下載APP，體驗更多樂趣」）使用 overflow:hidden + ellipsis 的設計性裁切，
        # 屬於合理版面。過濾 overflow:hidden 元素，僅檢測未設 overflow 控制卻溢出的節點。
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
        assert overflow_nodes == [], f"發現未設裁切控制卻溢出的文案節點：{overflow_nodes}"
        if sh: sh.full_page("verify_首頁文案無超框")

    def test_login_page_no_horizontal_overflow(self, page: Page, site_config):
        """WIN-VIS-005：登入頁沒有明顯橫向超框"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"登入頁橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"
        if sh: sh.full_page(f"verify_登入頁無橫向超框_sw{metrics['scrollWidth']}_iw{metrics['innerWidth']}")

    def test_login_form_alignment(self, page: Page, site_config):
        """WIN-VIS-006：登入表單對齊 — WAP 設計 inputs (有 padding) 與 buttons (填滿容器) 分群對齊。
        - inputs 之間：username / password x 與 width 對齊
        - buttons 之間：loginBtn / browseBtn x 與 width 對齊
        - inputs 相對 buttons 左邊界差距在合理 padding 範圍內（≤ 30px）
        """
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)

        # 先針對 input / button 各自截圖，讓 reviewer 能目視對齊狀況
        username_input = page.locator('input.login-input').nth(0)
        password_input = page.locator('input.login-input').nth(1)
        login_btn = page.locator('button.btn-login').first
        browse_btn = page.locator('button.btn-browse').first
        for loc, label in [
            (username_input, "verify_login_username_input對齊"),
            (password_input, "verify_login_password_input對齊"),
            (login_btn, "verify_login_登入按鈕對齊"),
            (browse_btn, "verify_login_先去逛逛按鈕對齊"),
        ]:
            loc.scroll_into_view_if_needed()
            if sh: sh.capture(loc, label)

        metrics = page.evaluate("""() => {
            const rect = el => {
                const box = el.getBoundingClientRect();
                return { x: box.x, width: box.width };
            };
            const inputs  = document.querySelectorAll('input.login-input');
            const loginBtn  = document.querySelector('button.btn-login');
            const browseBtn = document.querySelector('button.btn-browse');
            return {
                username:  rect(inputs[0]),
                password:  rect(inputs[1]),
                loginBtn:  rect(loginBtn),
                browseBtn: rect(browseBtn),
            };
        }""")
        # inputs 之間對齊：左邊界嚴格對齊；寬度允許 ≤ 30px 差異（password 右側 toggle 眼睛 icon 擠壓視覺寬度）
        input_xs     = [metrics["username"]["x"],     metrics["password"]["x"]]
        input_widths = [metrics["username"]["width"], metrics["password"]["width"]]
        assert max(input_xs)     - min(input_xs)     <= 2,  f"inputs 左邊界未對齊：{metrics}"
        assert max(input_widths) - min(input_widths) <= 30, f"inputs 寬度差異超過 icon 擠壓容忍（30px）：{metrics}"

        # buttons 之間嚴格對齊
        btn_xs     = [metrics["loginBtn"]["x"],     metrics["browseBtn"]["x"]]
        btn_widths = [metrics["loginBtn"]["width"], metrics["browseBtn"]["width"]]
        assert max(btn_xs)     - min(btn_xs)     <= 2, f"buttons 左邊界未對齊：{metrics}"
        assert max(btn_widths) - min(btn_widths) <= 2, f"buttons 寬度未一致：{metrics}"

        # inputs 左邊界相對 buttons 的 padding 落在合理範圍（WAP 實測 ≈ 19px）
        padding = metrics["username"]["x"] - metrics["loginBtn"]["x"]
        assert 0 <= padding <= 30, f"inputs/buttons 左邊界差距超過合理 padding：{padding}px"
        if sh: sh.full_page(f"verify_login表單整體對齊_padding{padding}px")

    def test_home_navbar_and_login_in_viewport(self, page: Page, site_config):
        """WIN-VIS-007：首頁分類 `.cat-btn` 與底部 tabbar 四個 tab（排行榜/公告/維護/個人）都在視窗內。
        WAP 無桌機版 `/Categories/` 連結；未登入首頁亦無登入 CTA，登入入口為底部「個人」tab。
        `.cat-btn` 首個元素允許 ≤ 16px 負偏移（WAP 橫滑 carousel 設計，實測「遊戲大廳」left≈-9.3px）。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)
        sh = get_screenshotter(page)

        EXPECTED_BOTTOM_TABS = ["排行榜", "公告", "維護", "個人"]
        CAT_LEFT_TOLERANCE = -16  # WAP 橫滑分類 carousel 首個元素輕微負偏移容忍

        # 先對前 5 個 .cat-btn 與四個底部 tabbar tab 截圖，確認 reviewer 能看到紅框標示
        cat_btns = page.locator('.cat-btn')
        for i in range(min(5, cat_btns.count())):
            cb = cat_btns.nth(i)
            cb.scroll_into_view_if_needed()
            text = (cb.inner_text() or "").strip()[:8] or f"idx{i}"
            if sh: sh.capture(cb, f"verify_首頁分類_{text}_viewport內")
        # 底部 tabbar 屬 fixed 元素，不需 scroll_into_view
        for label in EXPECTED_BOTTOM_TABS:
            tab = page.locator('.shadow-menubar .cursor-pointer', has_text=label).first
            if sh: sh.capture(tab, f"verify_底部tabbar_{label}tab_viewport內")

        metrics = page.evaluate("""(expectedTabs) => {
            const catBtns = [...document.querySelectorAll('.cat-btn')]
                .slice(0, 5)
                .map(el => {
                    const box = el.getBoundingClientRect();
                    return { text: (el.textContent || '').trim(), left: box.left, right: box.right, top: box.top };
                });
            const tabNodes = [...document.querySelectorAll('.shadow-menubar .cursor-pointer')];
            const bottomTabs = expectedTabs.map(label => {
                const el = tabNodes.find(n => (n.textContent || '').includes(label));
                if (!el) return { label, missing: true };
                const box = el.getBoundingClientRect();
                return { label, left: box.left, right: box.right, top: box.top };
            });
            return { innerWidth: window.innerWidth, catBtns, bottomTabs };
        }""", EXPECTED_BOTTOM_TABS)

        assert len(metrics["catBtns"]) >= 5, f"首頁 .cat-btn 不足 5 個：{metrics['catBtns']}"
        for item in metrics["catBtns"]:
            assert item["left"]  >= CAT_LEFT_TOLERANCE,        f"cat-btn 超出左邊界容忍（{CAT_LEFT_TOLERANCE}px）：{item}"
            assert item["right"] <= metrics["innerWidth"] + 1, f"cat-btn 超出右邊界：{item}"
            assert item["top"]   >= 0,                         f"cat-btn 超出上邊界：{item}"

        missing_tabs = [t["label"] for t in metrics["bottomTabs"] if t.get("missing")]
        assert not missing_tabs, f"bottom tabbar 缺少 tab：{missing_tabs}（預期：{EXPECTED_BOTTOM_TABS}）"
        for tab in metrics["bottomTabs"]:
            assert tab["left"]  >= 0,                         f"底部 {tab['label']} tab 超出左邊界：{tab}"
            assert tab["right"] <= metrics["innerWidth"] + 1, f"底部 {tab['label']} tab 超出右邊界：{tab}"
            assert tab["top"]   >= 0,                         f"底部 {tab['label']} tab 超出上邊界：{tab}"
        if sh: sh.full_page("verify_首頁分類與底部4tab皆在viewport內")
