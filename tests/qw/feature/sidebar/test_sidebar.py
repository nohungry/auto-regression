"""
QW 使用者選單（avatar-menu dropdown）結構測試（LM來財娛樂城）
QW-TC-S01 ~ QW-TC-S02

QW 無 KS 式的右側 drawer；user menu 為 avatar-trigger hover 後展開的
.avatar-menu__panel（dropdown）。

probe 2026-06-25：panel 內含 .avatar-menu__item（DIV）和 button.avatar-menu__logout：
  帳戶管理、VIP特權、紅利禮包、銀行卡管理、帳戶明細、投注紀錄、
  實時返水、全民代理、消息中心、個人信息、登出（繁體）

本檔驗「選單 UI 結構完整性」（開啟 + 預期項目齊全），與 member feature 區隔。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("qw")

# 選單應包含的代表性項目（probe 2026-06-25 繁體確認）
# 不包含罕見或可能隨語系變動的文案；帳戶管理/全民代理/消息中心/登出為代表
EXPECTED_ITEMS = ["帳戶管理", "VIP特權", "全民代理", "消息中心", "登出"]


@pytest.mark.p1
@pytest.mark.qw
class TestSidebar:
    """QW avatar-menu dropdown 選單結構（class_logged_in_page + go_home）"""

    def test_user_menu_opens(self, class_logged_in_page: Page, go_home):
        """QW-TC-S01：hover avatar 後 dropdown 正常展開且有內容"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        if sh: sh.capture(home.avatar_trigger, "before_open_menu")
        home.open_user_menu()

        panel = page.locator('.avatar-menu__panel')
        if sh: sh.capture(panel, "verify_選單開啟")

        texts = home.user_menu_item_texts()
        if sh: sh.full_page(f"verify_menu_items_{len(texts)}項")
        assert len(texts) > 3, f"選單項目過少，疑未正常展開：{texts}"

    def test_user_menu_sections(self, class_logged_in_page: Page, go_home):
        """QW-TC-S02：dropdown 含帳戶管理/VIP特權/全民代理/消息中心/登出等預期項目"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_user_menu()
        texts = home.user_menu_item_texts()
        panel = page.locator('.avatar-menu__panel')
        if sh: sh.capture(panel, f"verify_選單項目_found{len(texts)}")
        if sh: sh.full_page(f"verify_選單項目列表_{len(texts)}項")
        missing = [label for label in EXPECTED_ITEMS if label not in texts]
        assert not missing, (
            f"選單缺少預期項目：{missing}，實際：{texts}"
        )
