"""
多語系文案驗證 — 側邊欄選單項目
DRC-I18N-SIDEBAR-001~006

DRC 側邊欄（.sidebar-item）對應 DLT 的 hamburger drawer：
- sidebar container 為 CSS width=0（隱藏），但 DOM 中仍有文字
- 使用 expect(body).to_contain_text() 驗證（不需 scroll/click）
- 不需登入，sidebar 文字在未登入狀態下即存在於 DOM
"""

import pytest
from playwright.sync_api import Page, expect
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_announcement_popup_if_present
from utils.screenshot_helper import get_screenshotter


_SIDEBAR_LOCALE_CHECKS = [
    # (case_id, lang_name, personal_info, game_detail, inbox)
    ("DRC-I18N-SIDEBAR-001", "繁體中文",   "個人資訊",           "遊戲明細",          "站內信"),
    ("DRC-I18N-SIDEBAR-002", "簡体中文",   "个人信息",           "游戏明细",          "站内信"),
    ("DRC-I18N-SIDEBAR-003", "日本語",     "個人情報",           "ゲーム履歴",        "サイト内メール"),
    ("DRC-I18N-SIDEBAR-004", "ภาษาไทย",   "ข้อมูลส่วนตัว",     "รายละเอียดเกม",   "กล่องข้อความ"),
    ("DRC-I18N-SIDEBAR-005", "Tiếng Việt", "Thông tin cá nhân", "Chi tiết trò chơi", "Thư nội bộ"),
    ("DRC-I18N-SIDEBAR-006", "English",    "Profile",           "Game History",      "Inbox"),
]


def _switch_language(page: Page, url: str, lang_name: str):
    """前往首頁 → dismiss 彈窗 → globe icon 切換語系"""
    page.goto(url, wait_until="networkidle")
    dismiss_server_error_if_present(page)
    dismiss_announcement_popup_if_present(page, timeout=3000)
    globe = page.locator("img[src*='global']")
    globe.scroll_into_view_if_needed()
    globe.click()
    lang_option = page.locator("p.whitespace-nowrap", has_text=lang_name).first
    lang_option.wait_for(state="visible", timeout=5000)
    lang_option.click()
    page.wait_for_load_state("networkidle")
    dismiss_server_error_if_present(page)


@pytest.mark.p1
@pytest.mark.i18n
@pytest.mark.language
class TestI18NSidebar:
    """DRC-I18N-SIDEBAR-001~006：各語系側邊欄選單文案驗證"""

    @pytest.mark.parametrize("case_id,lang_name,personal_info,game_detail,inbox",
                             _SIDEBAR_LOCALE_CHECKS,
                             ids=[c[0] for c in _SIDEBAR_LOCALE_CHECKS])
    def test_sidebar_locale_text(self, page: Page, site_config, case_id, lang_name,
                                  personal_info, game_detail, inbox):
        """各語系側邊欄選單項目文案正確顯示"""
        _switch_language(page, site_config.url, lang_name)

        sh = get_screenshotter(page)
        body = page.locator("body")
        expect(body).to_contain_text(personal_info)
        expect(body).to_contain_text(game_detail)
        expect(body).to_contain_text(inbox)
        if sh: sh.full_page(f"verify_{lang_name}_sidebar文案")
