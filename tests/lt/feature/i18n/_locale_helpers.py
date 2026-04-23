"""
LT 多語系測試共用 helpers
移植自 tests/lt/test_locale_visual_matrix.py（已停用）

此模組提供：
- LOCALES / LOCALE_IDS：語系清單（所有 i18n 測試皆會 import）
- LOCALE_LABELS：會員 `/member-center` 各語系文案對照（bettingRecord / memberInfo / maintenance）
- collect_overflow_issues / assert_no_overflow：環境無關的 DOM 超框偵測（PR5 locale_layout 使用）
- login_with_locale：5 語系登入流程（PR4/PR5 使用）
- open_member_menu：進入 `/member-center`（WAP 底部「個人」tab，命名保留以維持既有 test import 相容）
- open_member_screen：進 `/member-center` 後 scroll 至指定 section（bettingRecord/memberInfo heading 或 maintenance 按鈕）

WAP 多語系實測現況（2026-04-22 probe）：
- 首頁 nav 文案（.cat-btn、底部 tabbar）所有語系都固定顯示繁中，未套 i18n。
- 登入頁 input placeholder 有正確 5 語系翻譯；
  `button.btn-login` 固定「立即登入」、`button.btn-browse` 固定「先去逛逛」、
  `span.lang-text` 固定「繁中」，均為產品現況已知固定文案（非測試 bug）。
"""

from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.lt.login_page import LoginPage
from pages.lt.home_page import HomePage


# 語系清單（id, 中文描述）
LOCALES = [
    ("tw", "繁中"),
    ("cn", "簡中"),
    ("en", "英文"),
    ("th", "泰文"),
    ("vn", "越文"),
]
LOCALE_IDS = [loc for loc, _ in LOCALES]

# 各語系 `/member-center` 文案對照
LOCALE_LABELS = {
    "tw": {"bettingRecord": "投注紀錄", "memberInfo": "會員訊息", "maintenance": "維護時間"},
    "cn": {"bettingRecord": "投注记录", "memberInfo": "会员讯息", "maintenance": "维护时间"},
    "en": {"bettingRecord": "Betting Record", "memberInfo": "Member Messages", "maintenance": "Maintenance Time"},
    "th": {"bettingRecord": "ประวัติการเดิมพัน", "memberInfo": "ข้อมูลสมาชิก", "maintenance": "ช่วงเวลาบำรุงรักษา"},
    "vn": {"bettingRecord": "Lịch sử cược", "memberInfo": "Tài khoản", "maintenance": "Bảo trì"},
}

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
    """WAP：等 networkidle + 底部 tabbar render 後，tap「個人」進入 `/member-center`。命名保留以相容既有 test import。

    與 `test_member_center_locale.py` 不同，本 helper 的 caller（如 `test_locale_reference.py`）不一定有明確 goto 首頁的步驟；
    登入完成後 SPA 可能停在過渡 state 而底部 tabbar 尚未 render，需在此補等待。
    """
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except PlaywrightTimeoutError:
        pass
    page.locator('.shadow-menubar').first.wait_for(state="visible", timeout=10000)
    HomePage(page).open_member_center()
    page.wait_for_timeout(500)


def open_member_screen(page: Page, locale: str, key: str) -> None:
    """WAP：進 `/member-center` 並 scroll 至指定 section。

    key：
    - `bettingRecord` / `memberInfo` → `p.font-bold` heading，locale 文案從 `LOCALE_LABELS` 取
    - `maintenance` → `button.bg-secondary.mb-5`（唯一 mb-5 class，locale-agnostic）
    """
    open_member_menu(page)
    if key == "maintenance":
        target = page.locator("button.bg-secondary.mb-5").first
    elif key in ("bettingRecord", "memberInfo"):
        target_text = LOCALE_LABELS[locale][key]
        target = page.locator("p.font-bold", has_text=target_text).first
    else:
        raise ValueError(f"不支援的 key：{key}（可用：bettingRecord / memberInfo / maintenance）")
    target.wait_for(state="visible", timeout=5000)
    target.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
