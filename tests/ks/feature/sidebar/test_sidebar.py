"""
KS 使用者選單（右側 drawer）結構測試（Super9娛樂城）
KS-TC-S01 ~ KS-TC-S02

KS user menu 為 hamburger 展開的右側 drawer（简体），內容比 LG 豐富：除 member 外
還有官方群组/官方频道、促销活动/每日签到/幸运转盘/实时返水、全民代理等。
本檔驗「選單 UI 結構完整性」（開啟 + 預期項目齊全），與 member feature 區隔。

probe 2026-06-07。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("ks")

# 選單應包含的代表性項目（官方群组 / member / 代理 / 会员讯息 / 登出；简体）
EXPECTED_ITEMS = ["官方群组", "我的帐号", "存款", "提现", "全民代理", "会员讯息", "登出"]


@pytest.mark.p1
@pytest.mark.ks
class TestSidebar:
    """KS 右側 drawer 選單結構（class_logged_in_page + go_home）"""

    def test_user_menu_opens(self, class_logged_in_page: Page, go_home):
        """KS-TC-S01：點 hamburger 後右側 drawer 正常展開且有內容"""
        page = class_logged_in_page
        home = HomePage(page)
        home.open_user_menu()
        sh = get_screenshotter(page)
        if sh: sh.capture(home.user_menu, "verify_選單開啟")
        texts = home.user_menu_item_texts()
        assert len(texts) > 3, f"選單項目過少，疑未正常展開：{texts}"

    def test_user_menu_sections(self, class_logged_in_page: Page, go_home):
        """KS-TC-S02：drawer 含官方群组/member/全民代理/会员讯息/登出等預期項目"""
        page = class_logged_in_page
        home = HomePage(page)
        home.open_user_menu()
        texts = home.user_menu_item_texts()
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_選單項目_{len(texts)}項")
        missing = [label for label in EXPECTED_ITEMS if label not in texts]
        assert not missing, f"選單缺少預期項目：{missing}，實際：{texts}"
