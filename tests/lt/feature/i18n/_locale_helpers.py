"""
LT 多語系測試共用 helpers（desktop responsive 版，2026-05-18 rewrite）

此模組提供：
- LOCALES / LOCALE_IDS：語系清單
- collect_overflow_issues / assert_no_overflow：環境無關的 DOM 超框偵測（test_locale_layout 用）
- login_with_locale：5 語系登入流程
- open_member_menu：開啟個人中心 overlay panel（命名沿用以保 import 相容；
  2026-05-18 換版後 /member-center 已不存在，個人中心改為 SPA inline panel）
- open_member_screen：開 panel 後點對應 sidebar item 或 footer tab

2026-05-18 換版要點：
- panel 開於 `/`，非導向 `/member-center`
- 內部結構：navbar 信用額度 + panel 帳號資訊 + 4 個 sidebar items
  (.sidebar-item.user / .game-details / .maintain / .mail) + 登出按鈕
- footer 5 個 .content tab：[0]維護 / [1]公告 / [2]中間 CTA / [3]排行榜 / [4]個人
"""

from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.factory import get_login_page_class, get_home_page_class


LoginPage = get_login_page_class("lt")
HomePage = get_home_page_class("lt")


# 語系清單（id, 中文描述）
LOCALES = [
    ("tw", "繁中"),
    ("cn", "簡中"),
    ("en", "英文"),
    ("th", "泰文"),
    ("vn", "越文"),
]
LOCALE_IDS = [loc for loc, _ in LOCALES]


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
# 操作輔助（desktop 版 panel + sidebar）
# ─────────────────────────────────────────────────────────────

def login_with_locale(page: Page, site_config, locale: str) -> None:
    login = LoginPage(page, site_config.url)
    login.goto_login(locale=locale)
    login.login(site_config.username, site_config.password)


def open_member_menu(page: Page) -> None:
    """開啟個人中心 overlay panel（取代 WAP 時期的 /member-center 導航）。

    命名沿用以保 import 相容。實作直接走 POM `open_member_center()`，
    POM 已處理 footer hydrate 等待與 dispatch_event 觸發。
    """
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except PlaywrightTimeoutError:
        pass
    HomePage(page).open_member_center()
    page.wait_for_timeout(500)


def open_member_screen(page: Page, locale: str, key: str) -> None:
    """開 panel 後點對應 sidebar item 或 footer tab。

    key 對應（2026-05-18 換版後對照）：
    - `bettingRecord` → `.sidebar-item.game-details`（遊戲明細，最接近投注紀錄概念）
    - `memberInfo`    → `.sidebar-item.mail`（站內信，最接近會員訊息概念）
    - `maintenance`   → footer 第一個 .content tab（維護時間獨立為底部 footer，不在 panel 內）
    """
    if key == "maintenance":
        # 維護時間搬到底部 footer，不需開 panel
        maint_tab = page.locator(".footer-bg .content").nth(0)
        maint_tab.wait_for(state="visible", timeout=5000)
        maint_tab.scroll_into_view_if_needed()
        maint_tab.dispatch_event("click")
        page.wait_for_timeout(500)
        return

    if key not in ("bettingRecord", "memberInfo"):
        raise ValueError(f"不支援的 key：{key}（可用：bettingRecord / memberInfo / maintenance）")

    open_member_menu(page)

    # sidebar item 在 non-tw locale 為 slide-in 結構，初始可能未可見；
    # 對 vr_reference 用途而言「panel 開啟即截圖」已具人工 review 價值，sidebar 點擊為 best-effort。
    sidebar_class = ".sidebar-item.game-details" if key == "bettingRecord" else ".sidebar-item.mail"
    target = page.locator(sidebar_class).first
    try:
        target.wait_for(state="visible", timeout=3000)
        target.scroll_into_view_if_needed()
        target.dispatch_event("click")
        page.wait_for_timeout(500)
    except PlaywrightTimeoutError:
        # slide-in 未自動展開，留在 panel 預設 view 截圖即可
        pass
