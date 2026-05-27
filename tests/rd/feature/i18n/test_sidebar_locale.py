"""
RD 多語系文案驗證 — 側邊欄選單項目 (狗狗娛樂城)
RD-I18N-SIDEBAR-001 ~ 005

驗證左側邊欄前 3 個選單項目（個人資訊 / 遊戲明細 / 站內信）的多語系文案。

RD 側邊欄結構與 RC 不同：
- 文字節點為 `p.opacity-0.lg:hidden`（lg viewport 上 display:none，但 DOM 中仍存在）
- 因此用 `body.to_contain_text()` 驗證文案（不需 hover / scroll，與 RC 同 pattern）

NOTE：dev-rd 簡体中文版部分文案使用繁體字（mixed 繁/簡），本測試以 dev 站當前文案為準（**as-is**）：
  - 簡体中文「我的帳戶」用繁體「帳」（應為「账」）
若產品端修正則此測試會 fail，視為 i18n regression 訊號。
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_dialog_mask_if_present
from utils.screenshot_helper import get_screenshotter


# (case_id, lang_name, personal_info, game_detail, inbox)
_SIDEBAR_LOCALE_CHECKS = [
    ("RD-I18N-SIDEBAR-001", "繁體中文",   "個人資訊",          "遊戲明細",          "站內信"),
    ("RD-I18N-SIDEBAR-002", "簡体中文",   "我的帳戶",          "游戏记录",          "信件"),
    ("RD-I18N-SIDEBAR-003", "日本語",     "マイアカウント",    "ゲーム履歴",        "メール"),
    ("RD-I18N-SIDEBAR-004", "Tiếng Việt", "Tài khoản của tôi", "Lịch sử trò chơi", "Thư"),
    ("RD-I18N-SIDEBAR-005", "English",    "My Account",        "Game records",      "Member message"),
]


def _switch_language(page: Page, base_url: str, lang_name: str):
    """前往首頁 → 關掉公告蓋板 → 點當前語言觸發按鈕 → 從 dropdown 選擇目標語言

    沿用 test_login_locale / test_home_locale 的 dispatch_event + retry pattern：
    - `button.bg-shade03` 觸發按鈕，filter 用任一已知語名（current state 不可預測）
    - 必須 `dispatch_event("click")`（hydration race + dialog-mask 攔截）
    - dropdown 沒展開則重試一次
    """
    import re as _re
    page.goto(base_url, wait_until="domcontentloaded")
    dismiss_server_error_if_present(page)
    dismiss_dialog_mask_if_present(page)

    lang_trigger = page.locator("button.bg-shade03").filter(
        has_text=_re.compile("繁體中文|簡体中文|日本語|Tiếng Việt|English")
    ).first
    expect(lang_trigger).to_be_visible(timeout=10000)
    lang_trigger.scroll_into_view_if_needed()

    target = page.locator("div.cursor-pointer p", has_text=lang_name).first
    lang_trigger.dispatch_event("click")
    try:
        target.wait_for(state="visible", timeout=3000)
    except PlaywrightTimeoutError:
        page.wait_for_timeout(2000)
        lang_trigger.dispatch_event("click")
        target.wait_for(state="visible", timeout=10000)
    target.dispatch_event("click")
    page.wait_for_timeout(1500)


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.i18n
@pytest.mark.language
class TestI18NSidebar:
    """RD-I18N-SIDEBAR-001 ~ 005：各語系側邊欄選單文案驗證"""

    @pytest.mark.parametrize(
        "case_id,lang_name,personal_info,game_detail,inbox",
        _SIDEBAR_LOCALE_CHECKS,
        ids=[c[0] for c in _SIDEBAR_LOCALE_CHECKS],
    )
    def test_sidebar_locale_text(self, page: Page, site_config, case_id, lang_name,
                                  personal_info, game_detail, inbox):
        """各語系側邊欄選單前 3 項（個人資訊 / 遊戲明細 / 站內信）文案正確顯示"""
        _switch_language(page, site_config.url, lang_name)

        sh = get_screenshotter(page)
        # 切完語系後再保險清一次蓋板
        dismiss_dialog_mask_if_present(page)

        # 整頁截圖（先存證據再做斷言）
        if sh: sh.full_page(f"verify_{lang_name}_sidebar文案_全貌")

        # sidebar 文字在 lg viewport 為 display:none，用 body.to_contain_text 驗（與 RC 一致）
        body = page.locator("body")
        expect(body).to_contain_text(personal_info)
        expect(body).to_contain_text(game_detail)
        expect(body).to_contain_text(inbox)

        # 額外針對 sidebar 區塊截圖（紅框可看出範圍）
        sidebar = page.locator("div.fixed").filter(has_text=personal_info).first
        if sidebar.count() > 0 and sh:
            sh.capture(sidebar, f"verify_{lang_name}_sidebar區塊_3項")
