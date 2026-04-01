"""
lt 站點 Functional / Visual Test
P1：功能驗證（重大版本必跑）
P2：視覺回歸（完整回歸才跑）

對應 Node.js 版：
  tests/public.spec.js        — WIN-PUB-004~006, 010~011
  tests/auth.spec.js          — WIN-AUTH-002, 004
  tests/i18n.spec.js          — WIN-I18N-001~005
  tests/copy.spec.js          — WIN-COPY-001~005
  tests/visual.spec.js        — WIN-VIS-001~007
  tests/visual-regression.spec.js — WIN-VR-001~003（p2，需先建立 baseline）

執行方式：
    .venv/bin/pytest tests/lt/test_functional.py -v
    .venv/bin/pytest tests/lt/test_functional.py -m p1 -v
    .venv/bin/pytest tests/lt/test_functional.py -m visual_regression --update-snapshots  # 建立 baseline
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.dlt.login_page import LoginPage
from pages.dlt.home_page import HomePage
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter


# ─────────────────────────────────────────────────────────────
# Visual Regression helper
# ─────────────────────────────────────────────────────────────

_BANNER_SELECTORS = [
    'img[src*="Page/Pc"]',       # banner carousel images
    'img[src*="MainPageImage"]', # platform game thumbnails
    'img[src*="Games/dlt/"]',    # locale-specific game grid thumbnails
    '[class*="banner"] img',
    '[class*="lg:via-[#FFF1A3]"]',
    '[class*="z-[98]"]',         # announcement bar container (dynamic text)
]

def _save_screenshot(img_bytes: bytes, name: str) -> None:
    """存檔截圖（不比對 baseline），供人工視覺確認用"""
    import os
    os.makedirs("screenshots/dlt/vr_reference", exist_ok=True)
    with open(f"screenshots/dlt/vr_reference/{name}", "wb") as f:
        f.write(img_bytes)


def _screenshot_with_mask(page: Page, selectors: list[str], full_page: bool = True) -> bytes:
    """隱藏動態元素後截圖，截圖後還原可見性。
    同時停止 Swiper carousel autoplay 並回到第一張，確保截圖一致。
    """
    page.evaluate("""(selectors) => {
        window.__masked = [];
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                window.__masked.push([el, el.style.visibility]);
                el.style.visibility = 'hidden';
            });
        });
        // 停止 Swiper autoplay 並回到第一張（避免 carousel 輪播造成截圖不一致）
        document.querySelectorAll('.swiper').forEach(el => {
            if (el.swiper) {
                el.swiper.autoplay.stop();
                el.swiper.slideTo(0, 0);
            }
        });
    }""", selectors)
    page.wait_for_timeout(300)
    try:
        return page.screenshot(full_page=full_page, animations="disabled")
    finally:
        page.evaluate("""() => {
            (window.__masked || []).forEach(([el, v]) => el.style.visibility = v);
            delete window.__masked;
        }""")


# ─────────────────────────────────────────────────────────────
# 公開頁延伸功能
# ─────────────────────────────────────────────────────────────

@pytest.mark.p1
@pytest.mark.dlt
class TestPublicFeatures:
    """WIN-PUB-004~006, 010~011：公開頁延伸功能"""

    def test_customer_service_visible(self, page: Page, site_config):
        """WIN-PUB-004：客服入口顯示"""
        login = LoginPage(page, site_config.url)
        login.goto()
        el = page.get_by_text("24小時客服").first
        expect(el).to_be_visible()
        sh = get_screenshotter(page)
        if sh: sh.capture(el, "verify_客服入口")

    def test_language_icon_visible(self, page: Page, site_config):
        """WIN-PUB-005：語系切換 icon 存在"""
        login = LoginPage(page, site_config.url)
        login.goto()
        el = page.locator('img[alt="Language"]').first
        expect(el).to_be_visible()
        sh = get_screenshotter(page)
        if sh: sh.capture(el, "verify_語系icon")

    def test_copyright_visible(self, page: Page, site_config):
        """WIN-PUB-006：版權資訊顯示"""
        login = LoginPage(page, site_config.url)
        login.goto()
        el = page.get_by_text("Copyright © 2025 LaiCai All rights reserved.").first
        expect(el).to_be_visible()
        sh = get_screenshotter(page)
        if sh: sh.capture(el, "verify_版權資訊")

    def test_customer_service_link_is_linee(self, page: Page, site_config):
        """WIN-PUB-010：客服連結指向 lin.ee"""
        login = LoginPage(page, site_config.url)
        login.goto()
        link = page.get_by_role("link", name="24小時客服").first
        expect(link).to_have_attribute("href", re.compile(r"lin\.ee"))
        sh = get_screenshotter(page)
        if sh: sh.capture(link, "verify_客服連結lin.ee")

    def test_browse_without_login_returns_home(self, page: Page, site_config):
        """WIN-PUB-011：登入頁「先去逛逛」可回首頁"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)

        browse_btn = page.get_by_role("button", name="先去逛逛")
        browse_btn.scroll_into_view_if_needed()
        if sh: sh.capture(browse_btn, "click_先去逛逛")
        browse_btn.click()

        expect(page).to_have_url(
            re.compile(r"^" + re.escape(site_config.url.rstrip("/")) + r"/?$"),
            timeout=5000,
        )
        expect(page.get_by_text("熱門", exact=True).first).to_be_visible()
        if sh: sh.full_page("verify_回到首頁")


# ─────────────────────────────────────────────────────────────
# 登入後功能
# ─────────────────────────────────────────────────────────────

@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.login
class TestAuthFeatures:
    """WIN-AUTH-002, 004：登入後功能驗證"""

    def test_member_features_text_visible(self, logged_in_page: Page):
        """WIN-AUTH-002：登入後會員功能文案存在（投注紀錄/會員訊息/維護時間/登出）"""
        home = HomePage(logged_in_page)
        home.open_member_drawer()
        sh = get_screenshotter(logged_in_page)
        for text in ["投注紀錄", "會員訊息", "維護時間", "登出"]:
            el = logged_in_page.get_by_text(text).first
            expect(el).to_be_visible()
            if sh: sh.capture(el, f"verify_會員功能_{text}")

    def test_category_navigation_after_login(self, logged_in_page: Page, site_config):
        """WIN-AUTH-004：登入後可切換真人與電子頁，帳號名稱仍顯示"""
        home = HomePage(logged_in_page)
        sh = get_screenshotter(logged_in_page)
        for label, url_pattern in [("真人", re.compile(r"/Categories/casino")),
                                    ("電子", re.compile(r"/Categories/slots"))]:
            home.click_nav_item(label)
            expect(logged_in_page).to_have_url(url_pattern, timeout=8000)
            username_el = logged_in_page.locator(
                '[class*="font-medium"]', has_text=site_config.username
            ).first
            expect(username_el).to_be_visible()
            if sh: sh.capture(username_el, f"verify_帳號顯示_{label}頁")


# ─────────────────────────────────────────────────────────────
# 多語系文案驗證
# ─────────────────────────────────────────────────────────────

_LOCALE_CHECKS = [
    ("WIN-I18N-001", "tw", ["熱門", "真人", "電子", "捕魚", "登入"],              "繁中首頁文案"),
    ("WIN-I18N-002", "cn", ["热门", "真人", "电子", "捕鱼", "登录"],              "簡中首頁文案"),
    ("WIN-I18N-003", "en", ["Hot", "Live Casino", "Slots", "Fishing", "Login"],  "英文首頁文案"),
    ("WIN-I18N-004", "th", ["ยอดฮิต", "คนจริง", "อิเล็กทรอนิกส์", "ยิงปลา", "เข้าสู่ระบบ"], "泰文首頁文案"),
    ("WIN-I18N-005", "vn", ["Phổ biến", "Người thật", "Điện tử", "Câu cá", "Đăng nhập"], "越文首頁文案"),
]


@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.i18n
class TestI18N:
    """WIN-I18N-001~005：多語系首頁文案驗證"""

    @pytest.mark.parametrize("case_id,locale,texts,title", _LOCALE_CHECKS,
                             ids=[c[0] for c in _LOCALE_CHECKS])
    def test_locale_home_text(self, page: Page, site_config, case_id, locale, texts, title):
        """各語系首頁主要文案正確顯示"""
        set_locale(page, site_config.url, locale)
        page.goto(site_config.url)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1500)

        sh = get_screenshotter(page)
        body = page.locator("body")
        for text in texts:
            expect(body).to_contain_text(text)
        if sh: sh.full_page(f"verify_{locale}_首頁文案")


# ─────────────────────────────────────────────────────────────
# 文案一致性驗證
# ─────────────────────────────────────────────────────────────

@pytest.mark.p1
@pytest.mark.dlt
@pytest.mark.copy
class TestCopy:
    """WIN-COPY-001~005：文案一致性驗證"""

    def test_home_title_and_footer(self, page: Page, site_config):
        """WIN-COPY-001：首頁標題與頁尾版權文案一致"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        expect(page).to_have_title("LM來財信用網")
        copyright_el = page.get_by_text("Copyright © 2025 LaiCai All rights reserved.").first
        expect(copyright_el).to_be_visible()
        if sh: sh.capture(copyright_el, "verify_版權文案")

    def test_login_page_placeholder_and_cta(self, page: Page, site_config):
        """WIN-COPY-002：登入頁 placeholder 與 CTA 文案正確"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        sh = get_screenshotter(page)

        username_input = page.get_by_placeholder("請填寫4-10位的字母或數字")
        password_input = page.get_by_placeholder("請填寫 8-20 位的字母或數字")

        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()
        expect(page.get_by_role("button", name="登入")).to_contain_text("登入")
        expect(page.get_by_role("button", name="先去逛逛")).to_contain_text("先去逛逛")
        if sh: sh.capture(username_input, "verify_帳號placeholder")
        if sh: sh.capture(password_input, "verify_密碼placeholder")

    def test_login_page_field_labels(self, page: Page, site_config):
        """WIN-COPY-003：登入頁欄位標籤文案正確（會員登入/會員帳號/登入密碼）"""
        login = LoginPage(page, site_config.url)
        login.goto_login()

        body = page.locator("body")
        for text in ["會員登入", "會員帳號", "登入密碼"]:
            expect(body).to_contain_text(text)
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_登入頁欄位標籤")

    def test_login_page_disclaimer(self, page: Page, site_config):
        """WIN-COPY-004：登入頁免責聲明文案存在"""
        login = LoginPage(page, site_config.url)
        login.goto_login()

        body = page.locator("body")
        expect(body).to_contain_text("登入即表示您已閱讀並同意本平台之")
        expect(body).to_contain_text("免責聲明")
        expect(body).to_contain_text("如不同意請勿使用本服務")
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_免責聲明文案")

    def test_home_category_order(self, page: Page, site_config):
        """WIN-COPY-005：首頁四個主分類文案順序一致（熱門/真人/電子/捕魚）"""
        login = LoginPage(page, site_config.url)
        login.goto()

        nav_texts = page.locator('a[href^="/Categories/"]').evaluate_all(
            """links => links
                .map(link => (link.textContent || '').trim())
                .filter(Boolean)
                .slice(0, 4)"""
        )
        assert nav_texts == ["熱門", "真人", "電子", "捕魚"], \
            f"分類順序不符，實際：{nav_texts}"
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_分類文案順序")


# ─────────────────────────────────────────────────────────────
# 視覺健康度驗證（DOM metrics，非截圖比對）
# ─────────────────────────────────────────────────────────────

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
            assert item["left"]  >= 0,                       f"元素超出左邊界：{item}"
            assert item["right"] <= metrics["innerWidth"] + 1, f"元素超出右邊界：{item}"
            assert item["top"]   >= 0,                       f"元素超出上邊界：{item}"


# ─────────────────────────────────────────────────────────────
# 視覺截圖回歸（p2，需先建立 baseline）
# 執行前請先跑：pytest tests/lt/test_functional.py -m visual_regression --update-snapshots
# ─────────────────────────────────────────────────────────────

@pytest.mark.p2
@pytest.mark.dlt
@pytest.mark.visual_regression
class TestVisualRegression:
    """WIN-VR-001~003：截圖 baseline 比對"""

    def test_home_shell_screenshot(self, page: Page, site_config):
        """WIN-VR-001：首頁 shell 截圖存檔（不比對，首頁含動態內容）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(2000)
        _save_screenshot(_screenshot_with_mask(page, _BANNER_SELECTORS), "lt-home-shell.png")

    def test_login_page_screenshot(self, page: Page, site_config, assert_snapshot):
        """WIN-VR-002：登入頁表單截圖比對"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        page.wait_for_timeout(1500)
        assert_snapshot(page.screenshot(animations="disabled"), name="lt-login-panel.png")

    def test_navbar_screenshot(self, page: Page, site_config, assert_snapshot):
        """WIN-VR-003：首頁上方導覽列截圖比對"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.wait_for_timeout(1500)
        navbar = page.locator('[class*="bg-navbar"]').first
        assert_snapshot(navbar.screenshot(animations="disabled"), name="lt-top-nav.png")
