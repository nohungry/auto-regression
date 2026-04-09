"""
DRC 視覺健康度驗證（DOM metrics，非截圖比對）
與 tests/dlt/feature/visual/test_visual.py 意圖對齊，selector 依 DRC 站實作調整。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.drc.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.visual
class TestVisual:
    """DRC 視覺健康度驗證（版面、破圖、對齊）"""

    def test_home_no_horizontal_overflow(self, page: Page, site_config):
        """首頁沒有明顯橫向超框（scrollWidth <= innerWidth + 4）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"

    def test_home_no_broken_images(self, page: Page, site_config):
        """首頁圖片資源沒有明顯破圖（complete 且 naturalWidth=0）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)

        broken = page.locator("img").evaluate_all("""imgs =>
            imgs
                .map(img => ({ src: img.getAttribute('src'), complete: img.complete, naturalWidth: img.naturalWidth }))
                .filter(img => img.complete && img.naturalWidth === 0 && img.src)
        """)
        assert broken == [], f"發現破圖：{broken}"

    def test_home_text_not_clipped(self, page: Page, site_config):
        """首頁主要文案區塊未明顯被裁切（scrollWidth - clientWidth <= 20）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)

        overflow_nodes = page.evaluate("""() => {
            const targets = Array.from(document.querySelectorAll('a, button, p, span, h1, h2, h3'));
            return targets
                .map(el => {
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

    def test_login_modal_no_horizontal_overflow(self, page: Page, site_config):
        """登入表單開啟後頁面沒有明顯橫向超框"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        page.wait_for_timeout(500)

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"登入表單橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"

    def test_login_form_alignment(self, page: Page, site_config):
        """登入表單帳號/密碼輸入框左右對齊（x 誤差 ≤ 2px，寬度誤差 ≤ 2px）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()

        metrics = page.evaluate("""() => {
            const rect = el => {
                if (!el) return null;
                const box = el.getBoundingClientRect();
                return { x: box.x, width: box.width };
            };
            return {
                username: rect(document.querySelector('input[placeholder="用戶名"]')),
                password: rect(document.querySelector('input[placeholder="密碼"]')),
            };
        }""")
        assert all(metrics.values()), f"登入表單輸入框未全部出現：{metrics}"
        xs     = [v["x"]     for v in metrics.values()]
        widths = [v["width"] for v in metrics.values()]
        assert max(xs)     - min(xs)     <= 2, f"左邊界未對齊：{metrics}"
        assert max(widths) - min(widths) <= 2, f"寬度未一致：{metrics}"

    def test_home_avatar_or_login_in_viewport(self, logged_in_page: Page, site_config):
        """登入後右上角 avatar 應在視窗內（未超出左右邊界）"""
        page = logged_in_page
        metrics = page.evaluate("""() => {
            const avatar = document.querySelector('img[alt="avatar"]');
            if (!avatar) return null;
            const box = avatar.getBoundingClientRect();
            return {
                innerWidth: window.innerWidth,
                left: box.left, right: box.right, top: box.top,
            };
        }""")
        assert metrics, "找不到 avatar"
        assert metrics["left"]  >= 0,                         f"avatar 超出左邊界：{metrics}"
        assert metrics["right"] <= metrics["innerWidth"] + 1, f"avatar 超出右邊界：{metrics}"
        assert metrics["top"]   >= 0,                         f"avatar 超出上邊界：{metrics}"
