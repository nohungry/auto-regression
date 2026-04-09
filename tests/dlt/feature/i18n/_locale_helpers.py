"""
DLT 多語系測試共用 helpers
移植自 tests/dlt/test_locale_visual_matrix.py（已停用）

此模組提供：
- LOCALES / LOCALE_LABELS 語系清單與各語系 drawer 文案對照
- collect_overflow_issues / assert_no_overflow 環境無關的 DOM 超框偵測
- login_with_locale / open_member_menu / open_member_screen 操作輔助
"""

from __future__ import annotations

from playwright.sync_api import Page

from pages.dlt.login_page import LoginPage


# 語系清單（id, 中文描述）
LOCALES = [
    ("tw", "繁中"),
    ("cn", "簡中"),
    ("en", "英文"),
    ("th", "泰文"),
    ("vn", "越文"),
]
LOCALE_IDS = [loc for loc, _ in LOCALES]

# 各語系 drawer 選單項目文案
LOCALE_LABELS = {
    "tw": {"bettingRecord": "投注紀錄", "memberInfo": "會員訊息", "maintenance": "維護時間"},
    "cn": {"bettingRecord": "投注记录", "memberInfo": "会员讯息", "maintenance": "维护时间"},
    "en": {"bettingRecord": "Betting Record", "memberInfo": "Member Messages", "maintenance": "Maintenance Time"},
    "th": {"bettingRecord": "ประวัติการเดิมพัน", "memberInfo": "ข้อมูลสมาชิก", "maintenance": "ช่วงเวลาบำรุงรักษา"},
    "vn": {"bettingRecord": "Lịch sử cược", "memberInfo": "Tài khoản", "maintenance": "Bảo trì"},
}

# 會員 drawer 結構 selector（語系無關）
DRAWER_XPATH = 'xpath=//*[.//img[@alt="Exit"] and .//img[@alt="Avatar"]]'

# 銀幕尺寸變動時仍合理出現的跑馬燈/固定文案，overflow 檢查時忽略
IGNORED_KEYWORDS = [
    "最新公告", "NEWS", "Thông báo mới nhất", "ประกาศล่าสุด",
    "歡迎貴賓蒞臨", "[ประกาศล่าสุด]", "24小時客服", "客服", "CS",
]


# ─────────────────────────────────────────────────────────────
# Overflow 偵測（環境無關 — 只看 scroll vs client 與 innerWidth）
# ─────────────────────────────────────────────────────────────

_OVERFLOW_JS = r"""
(ignoredKeywords) => {
    const selectors = ['button', 'a', 'p', 'span', 'label', '[role="tab"]', '[role="button"]'];

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
            const text = (el.textContent || '').trim().replace(/\s+/g, ' ');
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
}
"""


def collect_overflow_issues(page: Page) -> list:
    """回傳可能超框的元素清單（空清單 = 正常）。不依賴 pixel 座標。"""
    return page.evaluate(_OVERFLOW_JS, IGNORED_KEYWORDS)


def assert_no_overflow(page: Page, context_label: str) -> None:
    issues = collect_overflow_issues(page)
    assert issues == [], f"{context_label} 發現可能超框/跑版元素：{issues}"


# ─────────────────────────────────────────────────────────────
# 操作輔助
# ─────────────────────────────────────────────────────────────

def login_with_locale(page: Page, site_config, locale: str) -> None:
    login = LoginPage(page, site_config.url)
    login.goto_login(locale=locale)
    login.login(site_config.username, site_config.password)


def open_member_menu(page: Page) -> None:
    hamburger = page.locator(".hamburger").first
    hamburger.scroll_into_view_if_needed()
    hamburger.click()
    page.locator(DRAWER_XPATH).last.wait_for(state="visible", timeout=5000)
    page.wait_for_timeout(1000)


def open_member_screen(page: Page, locale: str, key: str) -> None:
    """開啟會員 drawer 並切換至指定分頁。drawer 按鈕在 viewport 外，使用 dispatch_event。"""
    open_member_menu(page)
    target_text = LOCALE_LABELS[locale][key]
    menu_item = page.get_by_text(target_text, exact=True).last
    menu_item.wait_for(state="visible", timeout=5000)
    menu_item.dispatch_event("click")
    page.wait_for_timeout(2000)
    drawer_text = page.locator(DRAWER_XPATH).last.inner_text()
    assert target_text in drawer_text, \
        f"Drawer 未顯示 {target_text} 內容，實際：{drawer_text[:200]}"
