"""
LG 使用者選單（avatar dropdown）結構測試（大撈家娛樂城）
LG-TC-S01 ~ LG-TC-S02

LG 無 RE 那種 t9 常駐側欄；其 user menu 為 avatar 右側滑入 dropdown。
本檔驗「選單 UI 結構完整性」（開啟 + 預期項目齊全），與 member feature 的
「點連結導航到會員頁」區隔——這裡只驗選單本身呈現正確。

probe 2026-06-07：LG dropdown 內容為 member-center 連結 + 登出。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lg")

# 選單應包含的代表性項目（member-center + 登出）
EXPECTED_ITEMS = ["我的帳戶", "帳戶明細", "投注紀錄", "會員訊息", "登出"]


@pytest.mark.p1
@pytest.mark.lg
class TestSidebar:
    """LG avatar dropdown 選單結構（class_logged_in_page + go_home）"""

    def test_user_menu_opens(self, class_logged_in_page: Page, go_home):
        """LG-TC-S01：點 avatar 後 dropdown 正常展開且有內容"""
        page = class_logged_in_page
        home = HomePage(page)
        home.open_user_menu()
        sh = get_screenshotter(page)
        if sh: sh.capture(home.user_menu, "verify_選單開啟")
        texts = home.user_menu_item_texts()
        assert len(texts) > 3, f"選單項目過少，疑未正常展開：{texts}"

    def test_user_menu_sections(self, class_logged_in_page: Page, go_home):
        """LG-TC-S02：dropdown 含預期 member-center 項目與登出"""
        page = class_logged_in_page
        home = HomePage(page)
        home.open_user_menu()
        texts = home.user_menu_item_texts()
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_選單項目_{len(texts)}項")
        missing = [label for label in EXPECTED_ITEMS if label not in texts]
        assert not missing, f"選單缺少預期項目：{missing}，實際：{texts}"
