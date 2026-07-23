"""
QW 視覺健康度驗證（DOM metrics，非截圖比對）— LM來財娛樂城
QW-VIS-001~006

與 tests/rc/feature/visual/test_visual.py 意圖對齊，selector / 流程依 QW 站實作調整。

QW 站差異：
- 框架 Nuxt (Vue)，多語系（LaiBetLanguage cookie）→ 全部走 CSS-based selector，不綁文案
- 登入非 modal：獨立 /auth 頁（LoginPage.goto() 直接導向 /auth）→ 原 rc 的兩條
  「login_modal」改為 /auth 頁版本（QW-VIS-004/005）
- 首頁 goto 用 domcontentloaded（背景 polling 不進 networkidle），公告 popup-mask
  需先 dismiss（HomePage.dismiss_any_popups）
- 登入指標為 avatar（img[alt="avatar"]，與 rc 巧合同 alt）
- 破圖檢查沿用 LT 防禦：排除 src='' 空圖（僅抓真·載入失敗）
"""

import pytest
from playwright.sync_api import Page
from pages.qw.login_page import LoginPage
from pages.qw.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p2
@pytest.mark.qw
@pytest.mark.visual
class TestVisual:
    """QW-VIS-001~006：視覺健康度驗證（版面、破圖、對齊）"""

    # ------------------------------------------------------------------
    # 站點適配 helper
    # ------------------------------------------------------------------

    def _open_home_page(self, page: Page, site_config):
        """導向 QW 首頁並清除公告 popup（QW LoginPage.goto 會導向 /auth，故首頁自行 goto）。"""
        page.goto(site_config.url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        HomePage(page).dismiss_any_popups()

    def _reach_login_form(self, page: Page, site_config) -> LoginPage:
        """QW 無 modal：直接導向獨立 /auth 頁（LoginPage.goto 內含 networkidle 保護 hydration）。"""
        login = LoginPage(page, site_config.url)
        login.goto()
        return login

    # ------------------------------------------------------------------
    # 首頁版面健康度
    # ------------------------------------------------------------------

    def test_home_no_horizontal_overflow(self, page: Page, site_config):
        """QW-VIS-001：首頁沒有明顯橫向超框（scrollWidth <= innerWidth + 4）"""
        self._open_home_page(page, site_config)
        sh = get_screenshotter(page)

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        if sh: sh.full_page(f"verify_首頁橫向超框檢測_sw{metrics['scrollWidth']}_iw{metrics['innerWidth']}")
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"

    def test_home_no_broken_images(self, page: Page, site_config):
        """QW-VIS-002：首頁圖片資源沒有明顯破圖（complete 且 naturalWidth=0）

        沿用 LT 防禦：排除 src='' 空圖（那屬 empty-src 站點 bug，非載入失敗），
        只抓「有 src 但 naturalWidth=0」的真·破圖。
        """
        self._open_home_page(page, site_config)
        page.wait_for_timeout(1000)
        sh = get_screenshotter(page)

        broken = page.locator("img").evaluate_all("""imgs =>
            imgs
                .map(img => ({ src: img.getAttribute('src'), complete: img.complete, naturalWidth: img.naturalWidth }))
                .filter(img => img.complete && img.naturalWidth === 0 && img.src && img.src !== '')
        """)
        total_imgs = page.locator("img").count()
        if sh: sh.full_page(f"verify_首頁破圖檢測_total{total_imgs}_broken{len(broken)}")
        assert broken == [], f"發現破圖：{broken}"

    def test_home_text_not_clipped(self, page: Page, site_config):
        """QW-VIS-003：首頁主要文案未明顯被裁切（允許 ellipsis 設計，排除 overflow:hidden 節點）"""
        self._open_home_page(page, site_config)
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

    # ------------------------------------------------------------------
    # 登入頁（/auth 獨立頁）版面健康度
    # ------------------------------------------------------------------

    def test_login_modal_no_horizontal_overflow(self, page: Page, site_config):
        """QW-VIS-004：登入頁（QW 為獨立 /auth 頁）沒有明顯橫向超框"""
        self._reach_login_form(page, site_config)
        sh = get_screenshotter(page)

        metrics = page.evaluate("""() => ({
            innerWidth: window.innerWidth,
            scrollWidth: document.documentElement.scrollWidth
        })""")
        if sh: sh.full_page(f"verify_auth頁橫向超框檢測_sw{metrics['scrollWidth']}_iw{metrics['innerWidth']}")
        assert metrics["scrollWidth"] <= metrics["innerWidth"] + 4, \
            f"/auth 頁橫向超框：scrollWidth={metrics['scrollWidth']}, innerWidth={metrics['innerWidth']}"

    def test_login_form_alignment(self, page: Page, site_config):
        """QW-VIS-005：/auth 頁帳號/密碼輸入框左右對齊（x 誤差 ≤ 2px，寬度誤差 ≤ 30px）

        寬度容忍 30px：密碼欄常含顯示/隱藏 toggle icon 擠壓視覺寬度（沿用 LT 版理由）。
        用 POM locator.bounding_box() 取座標，復用已驗證的 CSS selector。
        """
        login = self._reach_login_form(page, site_config)
        sh = get_screenshotter(page)

        boxes = {}
        for name, loc in [("username", login.username_input), ("password", login.password_input)]:
            loc.scroll_into_view_if_needed()
            if sh: sh.capture(loc, f"verify_{name}輸入框對齊")
            boxes[name] = loc.bounding_box()
        if sh: sh.full_page("verify_auth表單整體對齊檢測")

        assert all(boxes.values()), f"輸入框未全部出現：{boxes}"
        xs     = [b["x"]     for b in boxes.values()]
        widths = [b["width"] for b in boxes.values()]
        assert max(xs)     - min(xs)     <= 2,  f"左邊界未對齊：{boxes}"
        assert max(widths) - min(widths) <= 30, f"寬度差異超過 icon 擠壓容忍（30px）：{boxes}"

    # ------------------------------------------------------------------
    # 登入後 nav 指標視窗界限
    # ------------------------------------------------------------------

    def test_home_avatar_or_login_in_viewport(self, logged_in_page: Page, site_config):
        """QW-VIS-006：登入後 nav 登入指標（avatar）在視窗內（未超出左右/上邊界）"""
        page = logged_in_page
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_登入態首頁_pre_measure")

        indicator = HomePage(page).avatar
        indicator.scroll_into_view_if_needed()
        box = indicator.bounding_box()
        inner_width = page.evaluate("() => window.innerWidth")
        if sh: sh.capture(indicator, "verify_登入指標視窗界限檢測")

        assert box, "找不到登入指標（avatar）"
        assert box["x"]                >= 0,                f"指標超出左邊界：{box}"
        assert box["x"] + box["width"] <= inner_width + 1,  f"指標超出右邊界：box={box}, innerWidth={inner_width}"
        assert box["y"]                >= 0,                f"指標超出上邊界：{box}"
