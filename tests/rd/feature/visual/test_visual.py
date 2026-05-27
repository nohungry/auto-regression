"""
RD 視覺健康度驗證（DOM metrics，非截圖比對）— 狗狗娛樂城
與 RC `tests/rc/feature/visual/test_visual.py` 意圖對齊。

差異：
- 登入欄位 placeholder 用「帳號」「密碼」（RC 用「用戶名」）
- RD navbar 無 avatar（藏在「個人資訊」menu 內）→ 改測「登錄」按鈕在 viewport 內

每個 test 在 assertion 之前先輸出截圖證據（pass/fail 都拿得到）。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("rd")


@pytest.mark.p2
@pytest.mark.rd
@pytest.mark.visual
class TestVisual:
    """RD 視覺健康度驗證（版面、破圖、對齊）"""

    def test_home_no_horizontal_overflow(self, page: Page, site_config):
        """RD-VISUAL-001：首頁無明顯橫向超框（scrollWidth <= innerWidth + 4）"""
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        # 截圖在 assert 之前，label 帶實測數值（中性，pass/fail 都合理）
        if sh: sh.full_page(
            f"verify_首頁橫向超框檢測_inner{metrics['innerWidth']}_scroll{metrics['scrollWidth']}"
        )
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"

    def test_home_no_broken_images(self, page: Page, site_config):
        """RD-VISUAL-002：首頁無破圖（complete 且 naturalWidth=0）"""
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)

        result = page.evaluate("""() => {
            const imgs = Array.from(document.querySelectorAll('img'));
            const broken = imgs
                .map(img => ({
                    src: img.getAttribute('src'),
                    complete: img.complete,
                    naturalWidth: img.naturalWidth
                }))
                .filter(img => img.complete && img.naturalWidth === 0 && img.src);
            return { total: imgs.length, broken: broken };
        }""")
        if sh: sh.full_page(
            f"verify_首頁破圖檢測_total{result['total']}_broken{len(result['broken'])}"
        )
        assert result["broken"] == [], f"發現破圖：{result['broken']}"

    def test_home_text_not_clipped(self, page: Page, site_config):
        """RD-VISUAL-003：首頁主要文案未明顯被裁切（scrollWidth - clientWidth <= 20）"""
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)

        overflow_nodes = page.evaluate("""() => {
            const targets = Array.from(document.querySelectorAll('a, button, p, span, h1, h2, h3'));
            return targets
                .map(el => ({
                    text: (el.textContent || '').trim().slice(0, 40),
                    clientWidth: el.clientWidth,
                    scrollWidth: el.scrollWidth,
                }))
                .filter(item => item.text && item.clientWidth > 0 && item.scrollWidth - item.clientWidth > 20)
                .slice(0, 10);
        }""")
        if sh: sh.full_page(
            f"verify_首頁文案裁切檢測_overflow{len(overflow_nodes)}"
        )
        assert overflow_nodes == [], f"發現文案超框節點：{overflow_nodes}"

    def test_login_modal_no_horizontal_overflow(self, page: Page, site_config):
        """RD-VISUAL-004：登入 modal 開啟後頁面無橫向超框"""
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        page.wait_for_timeout(500)

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        if sh: sh.full_page(
            f"verify_登入modal橫向超框檢測_inner{metrics['innerWidth']}_scroll{metrics['scrollWidth']}"
        )
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"登入 modal 橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"

    def test_login_form_alignment(self, page: Page, site_config):
        """RD-VISUAL-005：登入表單帳號/密碼欄位左右對齊（x 誤差 ≤ 2px，寬度誤差 ≤ 2px）

        RD placeholder 為「帳號」「密碼」（與 RC 不同）。
        """
        sh = get_screenshotter(page)
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
                username: rect(document.querySelector('input[placeholder="帳號"]')),
                password: rect(document.querySelector('input[placeholder="密碼"]')),
            };
        }""")
        if sh: sh.full_page(
            f"verify_登入表單對齊檢測_user{metrics.get('username')}_pwd{metrics.get('password')}"
        )
        assert all(metrics.values()), f"登入表單輸入框未全部出現：{metrics}"
        xs = [v["x"] for v in metrics.values()]
        widths = [v["width"] for v in metrics.values()]
        assert max(xs) - min(xs) <= 2, f"左邊界未對齊：{metrics}"
        assert max(widths) - min(widths) <= 2, f"寬度未一致：{metrics}"

    def test_home_login_btn_in_viewport(self, page: Page, site_config):
        """RD-VISUAL-006：未登入時 navbar「登錄」按鈕應在視窗內（未超左右上邊界）

        RD navbar 不顯示 avatar（藏在「個人資訊」menu 內），改測「登錄」按鈕位置。
        """
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)
        login.goto()

        metrics = page.evaluate("""() => {
            // 找 navbar 上的「登錄」neon-btn
            const btn = Array.from(document.querySelectorAll('button.neon-btn'))
                .find(b => b.innerText.trim() === '登錄' && b.offsetParent !== null);
            if (!btn) return null;
            const box = btn.getBoundingClientRect();
            return {
                innerWidth: window.innerWidth,
                left: box.left, right: box.right, top: box.top,
            };
        }""")
        if sh: sh.full_page(f"verify_登錄按鈕viewport檢測_metrics{metrics}")
        assert metrics, "找不到 navbar 登錄按鈕"
        assert metrics["left"] >= 0, f"登錄按鈕超出左邊界：{metrics}"
        assert metrics["right"] <= metrics["innerWidth"] + 1, f"登錄按鈕超出右邊界：{metrics}"
        assert metrics["top"] >= 0, f"登錄按鈕超出上邊界：{metrics}"
