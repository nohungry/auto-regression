"""
LU 使用者選單（左側 sidebar）結構測試（Dlgbet）
LU-TC-S01 ~ LU-TC-S02

LU user menu 為 hamburger 展開的左側 sidebar，內容比 LG 豐富：除 member 外還有
官方頻道/官方群組、優惠/每日獎金/輪盤、全民代理、兌換碼、語言/音效等。
本檔驗「選單 UI 結構完整性」（開啟 + 預期項目齊全），與 member feature 區隔。

probe 2026-06-07。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lu")

# 選單應包含的代表性項目（官方頻道 / member / 代理 / 語言 / 登出）
EXPECTED_ITEMS = ["官方群組", "我的帳戶", "存款", "提現", "全民代理", "語言", "登出"]


@pytest.mark.p1
@pytest.mark.lu
class TestSidebar:
    """LU 左側 sidebar 選單結構（class_logged_in_page + go_home）"""

    def test_user_menu_opens(self, class_logged_in_page: Page, go_home):
        """LU-TC-S01：點 hamburger 後左側 sidebar 正常展開且有內容"""
        page = class_logged_in_page
        home = HomePage(page)
        home.open_user_menu()
        sh = get_screenshotter(page)
        if sh: sh.capture(home.user_menu, "verify_選單開啟")
        texts = home.user_menu_item_texts()
        assert len(texts) > 3, f"選單項目過少，疑未正常展開：{texts}"

    def test_user_menu_sections(self, class_logged_in_page: Page, go_home):
        """LU-TC-S02：sidebar 含官方頻道/member/全民代理/語言/登出等預期項目"""
        page = class_logged_in_page
        home = HomePage(page)
        home.open_user_menu()
        texts = home.user_menu_item_texts()
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_選單項目_{len(texts)}項")
        missing = [label for label in EXPECTED_ITEMS if label not in texts]
        assert not missing, f"選單缺少預期項目：{missing}，實際：{texts}"
