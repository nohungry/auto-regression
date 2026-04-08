"""
視覺健康度驗證（DOM metrics，非截圖比對）
WIN-VIS-001~007
"""

import pytest
from playwright.sync_api import Page, expect
from pages.dlt.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter
from tests.dlt.feature.visual.helpers import BANNER_SELECTORS


@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.visual
class TestVisual:
    """WIN-VIS-001~007：視覺健康度驗證（版面、破圖、對齊）"""

    def test_home_no_horizontal_overflow(self, page: Page, site_config):
        """WIN-VIS-001：首頁沒有明顯橫向超框（scrollWidth <= innerWidth + 4）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"

    def test_home_no_broken_images(self, page: Page, site_config):
        """WIN-VIS-002：首頁圖片資源沒有明顯破圖"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)

        broken = page.locator("img").evaluate_all("""imgs =>
            imgs
                .map(img => ({ src: img.getAttribute('src'), complete: img.complete, naturalWidth: img.naturalWidth }))
                .filter(img => img.complete && img.naturalWidth === 0)
        """)
        assert broken == [], f"發現破圖：{broken}"

    def test_home_banner_visible(self, page: Page, site_config):
        """WIN-VIS-003：首頁主要 banner 區塊可見"""
        login = LoginPage(page, site_config.url)
        login.goto()
        banner = page.locator(
            'img[src*="Page/Pc"], img[src*="MainPageImage"], [class*="banner"] img'
        ).first
        expect(banner).to_be_visible()
        sh = get_screenshotter(page)
        if sh: sh.capture(banner, "verify_banner區塊可見")

    def test_home_text_not_clipped(self, page: Page, site_config):
        """WIN-VIS-004：首頁主要文案區塊未明顯被裁切（scrollWidth - clientWidth <= 20）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)

        overflow_nodes = page.evaluate("""() => {
            const targets = Array.from(document.querySelectorAll('a, button, p, span, h1, h2, h3'));
            return targets
                .map(el => {
                    const style = window.getComputedStyle(el);
                    return {
                        text: (el.textContent || '').trim().slice(0, 40),
                        clientWidth: el.clientWidth,
                        scrollWidth: el.scrollWidth,
                    };
                })
                .filter(item => item.text && item.clientWidth > 0 && item.scrollWidth - item.clientWidth > 20)
                .slice(0, 10);
        }""")
        assert overflow_nodes == [], f"發現文案超框節點：{overflow_nodes}"

    def test_login_page_no_horizontal_overflow(self, page: Page, site_config):
        """WIN-VIS-005：登入頁沒有明顯橫向超框"""
        login = LoginPage(page, site_config.url)
        login.goto_login()

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"登入頁橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"

    def test_login_form_alignment(self, page: Page, site_config):
        """WIN-VIS-006：登入表單輸入框與按鈕左右對齊（x 座標誤差 ≤ 2px，寬度誤差 ≤ 2px）"""
        login = LoginPage(page, site_config.url)
        login.goto_login()

        metrics = page.evaluate("""() => {
            const rect = el => {
                const box = el.getBoundingClientRect();
                return { x: box.x, width: box.width };
            };
            const inputs  = document.querySelectorAll('input.input-style');
            const buttons = [...document.querySelectorAll('button')];
            return {
                username:    rect(inputs[0]),
                password:    rect(inputs[1]),
                loginBtn:    rect(buttons.find(b => (b.textContent || '').includes('登入'))),
                browseBtn:   rect(buttons.find(b => (b.textContent || '').includes('先去逛逛'))),
            };
        }""")
        xs     = [v["x"]     for v in metrics.values()]
        widths = [v["width"] for v in metrics.values()]
        assert max(xs)     - min(xs)     <= 2, f"左邊界未對齊：{metrics}"
        assert max(widths) - min(widths) <= 2, f"寬度未一致：{metrics}"

    def test_home_navbar_and_login_in_viewport(self, page: Page, site_config):
        """WIN-VIS-007：首頁桌機導覽列與登入 CTA 都在視窗內"""
        login = LoginPage(page, site_config.url)
        login.goto()

        metrics = page.evaluate("""() => {
            const navLinks = [...document.querySelectorAll('a[href^="/Categories/"]')]
                .slice(0, 4)
                .map(link => {
                    const box = link.getBoundingClientRect();
                    return { text: (link.textContent || '').trim(), left: box.left, right: box.right, top: box.top };
                });
            const loginButton = [...document.querySelectorAll('button')]
                .find(b => (b.textContent || '').includes('登入'));
            const loginBox = loginButton.getBoundingClientRect();
            return {
                innerWidth: window.innerWidth,
                navLinks,
                loginButton: { left: loginBox.left, right: loginBox.right, top: loginBox.top }
            };
        }""")
        for item in [*metrics["navLinks"], metrics["loginButton"]]:
            assert item["left"]  >= 0,                         f"元素超出左邊界：{item}"
            assert item["right"] <= metrics["innerWidth"] + 1, f"元素超出右邊界：{item}"
            assert item["top"]   >= 0,                         f"元素超出上邊界：{item}"
