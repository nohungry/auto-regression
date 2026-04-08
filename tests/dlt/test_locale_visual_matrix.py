"""
多語系視覺矩陣測試（Locale Visual Matrix）
5 語系 × 6 場景 = 30 tests（p2，截圖 baseline 比對 + overflow 驗證）

對應 Node.js 版：
  tests/locale-visual-matrix.spec.js — WIN-LVIS-TW/CN/EN/TH/VN-001~006

執行方式：
    # 首次建立 baseline（或更新）：
    .venv/bin/pytest tests/dlt/test_locale_visual_matrix.py --update-snapshots
    # 後續比對：
    .venv/bin/pytest tests/dlt/test_locale_visual_matrix.py -v
    .venv/bin/pytest tests/dlt/test_locale_visual_matrix.py -m locale_visual -v
"""

import pytest
from playwright.sync_api import Page
from pages.dlt.login_page import LoginPage

pytestmark = pytest.mark.skip(reason="多語系視覺測試暫緩，待穩定後恢復")


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
# 語系清單與各語系選單文案對照
# ─────────────────────────────────────────────────────────────

_LOCALES = [
    ("tw", "繁中"),
    ("cn", "簡中"),
    ("en", "英文"),
    ("th", "泰文"),
    ("vn", "越文"),
]

_LOCALE_IDS = [loc for loc, _ in _LOCALES]

# 各語系 drawer 選單項目文案
_LOCALE_LABELS = {
    "tw": {"bettingRecord": "投注紀錄", "memberInfo": "會員訊息", "maintenance": "維護時間"},
    "cn": {"bettingRecord": "投注记录", "memberInfo": "会员讯息", "maintenance": "维护时间"},
    "en": {"bettingRecord": "Betting Record", "memberInfo": "Member Messages", "maintenance": "Maintenance Time"},
    "th": {"bettingRecord": "ประวัติการเดิมพัน", "memberInfo": "ข้อมูลสมาชิก", "maintenance": "ช่วงเวลาบำรุงรักษา"},
    "vn": {"bettingRecord": "Lịch sử cược", "memberInfo": "Tài khoản", "maintenance": "Bảo trì"},
}

# 會員 drawer 結構 selector（語系無關）
_DRAWER_XPATH = 'xpath=//*[.//img[@alt="Exit"] and .//img[@alt="Avatar"]]'


# ─────────────────────────────────────────────────────────────
# 輔助函式
# ─────────────────────────────────────────────────────────────

def _collect_text_overflow_issues(page: Page) -> list:
    """移植自 JS collectTextOverflowIssues，回傳超框元素清單（空清單 = 正常）"""
    return page.evaluate("""() => {
        const selectors = ['button', 'a', 'p', 'span', 'label', '[role="tab"]', '[role="button"]'];
        const ignoredKeywords = [
            '最新公告', 'NEWS', 'Thông báo mới nhất', 'ประกาศล่าสุด',
            '歡迎貴賓蒞臨', '[ประกาศล่าสุด]', '24小時客服', '客服', 'CS',
        ];

        const hasAncestorMatching = (element, matcher) => {
            let current = element;
            while (current) {
                if (matcher(current)) return true;
                current = current.parentElement;
            }
            return false;
        };

        const isIgnoredStructure = (element) => {
            return hasAncestorMatching(element, (node) => {
                if (node.matches?.('a[href*="lin.ee"]')) return true;
                if (node.querySelector?.('img[alt="Annt"]')) return true;
                return false;
            });
        };

        const elements = Array.from(document.querySelectorAll(selectors.join(',')));
        return elements
            .map(el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                const text = (el.textContent || '').trim().replace(/\\s+/g, ' ');
                const visible = rect.width > 0 && rect.height > 0
                    && style.visibility !== 'hidden' && style.display !== 'none';
                return {
                    text, tag: el.tagName,
                    className: String(el.className || '').slice(0, 120),
                    left: Math.round(rect.left), right: Math.round(rect.right),
                    clientWidth: el.clientWidth, scrollWidth: el.scrollWidth,
                    clientHeight: el.clientHeight, scrollHeight: el.scrollHeight,
                    visible, ignoredStructure: isIgnoredStructure(el),
                };
            })
            .filter(item => item.visible && item.text.length >= 2)
            .filter(item => !item.ignoredStructure)
            .filter(item => !ignoredKeywords.some(kw => item.text.includes(kw)))
            .filter(item => (
                (item.scrollWidth  - item.clientWidth  > 8) ||
                (item.scrollHeight - item.clientHeight > 8) ||
                item.right > window.innerWidth + 2 ||
                item.left < -2
            ))
            .slice(0, 20);
    }""")


def _expect_no_overflow(page: Page, context_label: str):
    issues = _collect_text_overflow_issues(page)
    assert issues == [], f"{context_label} 發現可能超框/跑版元素：{issues}"


def _login_with_locale(page: Page, site_config, locale: str):
    """以指定語系登入，等待 SPA 跳轉至首頁"""
    login = LoginPage(page, site_config.url)
    login.goto_login(locale=locale)
    login.login(site_config.username, site_config.password)


def _open_member_menu(page: Page):
    """點擊漢堡選單，等待 drawer 展開（使用 img[alt="Exit"] 驗證，語系無關）"""
    hamburger = page.locator(".hamburger").first
    hamburger.scroll_into_view_if_needed()
    hamburger.click()
    page.locator(_DRAWER_XPATH).last.wait_for(state="visible", timeout=5000)
    page.wait_for_timeout(1000)


def _open_member_screen(page: Page, locale: str, key: str):
    """開啟會員 drawer → 點擊指定選單項目，驗證內容切換
    drawer 按鈕在 viewport 外，使用 dispatch_event("click")
    """
    _open_member_menu(page)
    target_text = _LOCALE_LABELS[locale][key]
    menu_item = page.get_by_text(target_text, exact=True).last
    menu_item.wait_for(state="visible", timeout=5000)
    menu_item.dispatch_event("click")
    page.wait_for_timeout(2000)
    # 驗證 drawer 內容已切換至目標頁
    drawer_text = page.locator(_DRAWER_XPATH).last.inner_text()
    assert target_text in drawer_text, \
        f"Drawer 未顯示 {target_text} 內容，實際：{drawer_text[:200]}"


# ─────────────────────────────────────────────────────────────
# 測試 Class
# ─────────────────────────────────────────────────────────────

@pytest.mark.p2
@pytest.mark.dlt
@pytest.mark.locale_visual
class TestLocaleVisualMatrix:
    """WIN-LVIS-TW/CN/EN/TH/VN-001~006：5 語系 × 6 場景截圖 + overflow 驗證"""

    @pytest.mark.parametrize("locale,locale_label", _LOCALES, ids=_LOCALE_IDS)
    def test_home_shell(self, page: Page, site_config, locale, locale_label):
        """WIN-LVIS-{LOCALE}-001：首頁 shell 截圖存檔 + overflow（截圖不比對，首頁含動態內容）"""
        login = LoginPage(page, site_config.url)
        login.goto(locale=locale)
        page.wait_for_timeout(3000)
        _save_screenshot(_screenshot_with_mask(page, _BANNER_SELECTORS), f"locale-{locale}-home-shell.png")
        _expect_no_overflow(page, f"{locale_label}首頁")

    @pytest.mark.parametrize("locale,locale_label", _LOCALES, ids=_LOCALE_IDS)
    def test_login_page(self, page: Page, site_config, assert_snapshot, locale, locale_label):
        """WIN-LVIS-{LOCALE}-002：登入頁表單與規章文案截圖 + overflow"""
        login = LoginPage(page, site_config.url)
        login.goto_login(locale=locale)
        page.wait_for_timeout(2000)
        assert_snapshot(page.screenshot(full_page=True, animations="disabled"), name=f"locale-{locale}-login-page.png")
        _expect_no_overflow(page, f"{locale_label}登入頁")

    @pytest.mark.parametrize("locale,locale_label", _LOCALES, ids=_LOCALE_IDS)
    def test_member_menu(self, page: Page, site_config, locale, locale_label):
        """WIN-LVIS-{LOCALE}-003：登入後會員側欄截圖存檔 + overflow（截圖不比對，背景含動態內容）"""
        _login_with_locale(page, site_config, locale)
        _open_member_menu(page)
        page.wait_for_timeout(1500)
        _save_screenshot(page.screenshot(full_page=True, animations="disabled"), f"locale-{locale}-member-menu.png")
        _expect_no_overflow(page, f"{locale_label}會員側欄")

    @pytest.mark.parametrize("locale,locale_label", _LOCALES, ids=_LOCALE_IDS)
    def test_betting_record(self, page: Page, site_config, assert_snapshot, locale, locale_label):
        """WIN-LVIS-{LOCALE}-004：投注紀錄頁截圖 + overflow"""
        _login_with_locale(page, site_config, locale)
        _open_member_screen(page, locale, "bettingRecord")
        page.wait_for_timeout(1500)
        assert_snapshot(page.screenshot(full_page=True, animations="disabled"), name=f"locale-{locale}-betting-record.png")
        _expect_no_overflow(page, f"{locale_label}投注紀錄頁")

    @pytest.mark.parametrize("locale,locale_label", _LOCALES, ids=_LOCALE_IDS)
    def test_member_info(self, page: Page, site_config, assert_snapshot, locale, locale_label):
        """WIN-LVIS-{LOCALE}-005：會員資料頁截圖 + overflow"""
        _login_with_locale(page, site_config, locale)
        _open_member_screen(page, locale, "memberInfo")
        page.wait_for_timeout(1500)
        assert_snapshot(page.screenshot(full_page=True, animations="disabled"), name=f"locale-{locale}-member-info.png")
        _expect_no_overflow(page, f"{locale_label}會員資料頁")

    @pytest.mark.parametrize("locale,locale_label", _LOCALES, ids=_LOCALE_IDS)
    def test_maintenance(self, page: Page, site_config, assert_snapshot, locale, locale_label):
        """WIN-LVIS-{LOCALE}-006：維護時間頁截圖 + overflow"""
        _login_with_locale(page, site_config, locale)
        _open_member_screen(page, locale, "maintenance")
        page.wait_for_timeout(1500)
        assert_snapshot(page.screenshot(full_page=True, animations="disabled"), name=f"locale-{locale}-maintenance.png")
        _expect_no_overflow(page, f"{locale_label}維護時間頁")
